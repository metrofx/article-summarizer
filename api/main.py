from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware  # Changed import
from fastapi.responses import JSONResponse
from ipaddress import ip_address, ip_network
from starlette.requests import Request
from pydantic import BaseModel, HttpUrl
from bs4 import BeautifulSoup
import requests
import trafilatura
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import json
from db import Cache
import logging
from fastapi.responses import HTMLResponse
from urllib.parse import unquote, urlparse  # Add urlparse import
from datetime import datetime, timedelta
from collections import defaultdict

# Load environment variables
load_dotenv(verbose=True)  # Add verbose=True for debugging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Log environment variables for debugging
# logger.info("Environment variables:")
# logger.info(f"ALLOWED_HOSTS env: {os.getenv('ALLOWED_HOSTS')}")
# logger.info(f"ALLOWED_IPS env: {os.getenv('ALLOWED_IPS')}")

# Get allowed hosts and IPs from environment variables with better error handling
def parse_ip_networks(ip_list: str) -> list:
    networks = []
    for ip in ip_list.split(","):
        try:
            networks.append(ip_network(ip.strip()))
        except ValueError as e:
            logger.error(f"Invalid IP/network in config: {ip.strip()}")
    return networks

# Define ALLOWED_HOSTS and ALLOWED_IPS before logging them
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
ALLOWED_IPS = parse_ip_networks(os.getenv("ALLOWED_IPS", "127.0.0.1/32"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")

# Print configuration at startup
logger.info("=== API Configuration ===")
logger.info(f"Allowed Hosts: {ALLOWED_HOSTS}")
logger.info(f"Allowed IPs: {[str(n) for n in ALLOWED_IPS]}")
logger.info(f"OpenRouter API Key configured: {'Yes' if OPENROUTER_API_KEY else 'No'}")
logger.info(f"OpenRouter Model: {OPENROUTER_MODEL}")
logger.info("=====================")

app = FastAPI()
cache = Cache()

# Add trusted hosts middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS
)

class IPRestrictionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        # Add debug logging
        logger.info(f"Request from IP: {client_ip}")
        logger.info(f"Allowed IPs: {ALLOWED_IPS}")
        logger.info(f"Request headers: {request.headers}")
        
        try:
            client_addr = ip_address(client_ip)
            if not any(client_addr in network for network in ALLOWED_IPS):
                logger.warning(f"Access denied for IP: {client_ip}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": f"Access denied."
                    }
                )
        except ValueError:
            logger.error(f"Invalid IP address: {client_ip}")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid IP address: {client_ip}"}
            )
        
        response = await call_next(request)
        return response

# Add IP restriction middleware
app.add_middleware(IPRestrictionMiddleware)

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class URLInput(BaseModel):
    url: HttpUrl

class ExtractResponse(BaseModel):
    url: str
    og_metadata: dict
    text_content: str
    cached: bool = False

class SummarizeRequest(BaseModel):
    text: str
    url: Optional[str] = None

class SummarizeResponse(BaseModel):
    summary: str
    cached: bool = False

class AnalyzeResponse(BaseModel):
    url: str
    og_metadata: dict
    content: Dict[str, str]
    cached: bool = False

class LatestArticlesResponse(BaseModel):
    articles: list[dict]

def extract_opengraph_metadata(url: str) -> dict:
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        metadata = {}
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))

        for tag in og_tags:
            property_name = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            metadata[property_name] = content

        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting OpenGraph metadata: {str(e)}")

def extract_text_content(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)

        # Configure trafilatura settings to exclude links and other elements
        config = {
            'include_links': False,
            'include_formatting': True,
            'include_images': False,
            'include_tables': True,
            'no_fallback': True,
            'output_format': 'markdown'
        }

        text = trafilatura.extract(downloaded, **config)
        return text if text else ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text content: {str(e)}")

async def summarize_text(text: str) -> str:
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""Summarize article text surrounded by <content> </content> tags into beautiful markdown formatted and structured key ideas, making it easy to read and comprehend. Determine the content language in it but don't mention it. Only respond in Bahasa Indonesia if content text is in Bahasa Indonesia. Otherwise, always respond in English. The answer should be concise, clear, and capture the important points of the content. Respond directly without any preamble or introductory statements. Do not inform that it's a summary. End with important quote taken from the article that is unique and capture attention.
<content>
{text}
</content>
"""

    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        # Log the request and response for debugging
        print("Request payload:", json.dumps(data, indent=2))
        print("Response status code:", e.response.status_code)
        print("Response body:", e.response.text)
        raise HTTPException(status_code=500, detail=f"Error summarizing text: {e.response.text}")

async def process_url(url: str) -> Dict[str, Any]:
    """
    Process a URL completely - extract text, metadata, and generate summary.
    This is the core function that handles all processing and caching.
    """
    logger.info(f"Processing URL: {url}")

    # Check cache first for complete data
    cached_data = cache.get_cached_article(url)

    # If we have complete cached data, return it
    if (cached_data and cached_data.get("text_content") and cached_data.get("summary") and cached_data.get("og_metadata")):
        logger.info(f"Found complete cached data for: {url}")
        return {
            "url": url,
            "og_metadata": cached_data["og_metadata"],
            "text_content": cached_data["text_content"],
            "summary": cached_data["summary"],
            "cached": True
        }

    # If not in cache or incomplete, process the URL
    try:
        # Extract metadata and text content
        og_metadata = cached_data.get("og_metadata") if cached_data else extract_opengraph_metadata(url)
        text_content = cached_data.get("text_content") if cached_data else extract_text_content(url)

        # Generate summary if needed
        if cached_data and cached_data.get("summary"):
            summary = cached_data["summary"]
        else:
            summary = await summarize_text(text_content)

        # Cache all the data
        cache.cache_article(url, text_content, summary, og_metadata)

        return {
            "url": url,
            "og_metadata": og_metadata,
            "text_content": text_content,
            "summary": summary,
            "cached": False
        }
    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class RateLimiter:
    def __init__(self):
        self.last_request_time = defaultdict(lambda: datetime.min)

    async def check_rate_limit(self, client_ip: str):
        now = datetime.now()
        time_since_last_request = now - self.last_request_time[client_ip]
        
        if time_since_last_request < timedelta(seconds=2):
            remaining_time = 2 - time_since_last_request.seconds
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Please try again later ({remaining_time})."
            )
        
        self.last_request_time[client_ip] = now

rate_limiter = RateLimiter()

# Create a dependency
async def check_rate_limit(request: Request):
    client_ip = request.client.host
    await rate_limiter.check_rate_limit(client_ip)

@app.post("/extract")
async def extract_url_content(
    url_input: URLInput,
    _: None = Depends(check_rate_limit)
) -> ExtractResponse:
    url = str(url_input.url)
    logger.info(f"Extract endpoint called for URL: {url}")

    try:
        # Process the URL completely
        result = await process_url(url)

        # Return only the extraction part
        return ExtractResponse(
            url=url,
            og_metadata=result["og_metadata"],
            text_content=result["text_content"],
            cached=result.get("cached", False)  # Use get() with default value
        )
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize")
async def summarize_content(
    request: SummarizeRequest,
    _: None = Depends(check_rate_limit)
) -> SummarizeResponse:
    logger.info("Summarize endpoint called")

    try:
        if request.url:
            # Process the URL completely
            result = await process_url(request.url)

            # Return only the summary part
            return SummarizeResponse(
                summary=result["summary"],
                cached=result["cached"]
            )
        else:
            # If no URL provided, just summarize the text without caching
            summary = await summarize_text(request.text)
            return SummarizeResponse(summary=summary)
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze")
async def analyze_url(
    url: str,
    _: None = Depends(check_rate_limit)
) -> AnalyzeResponse:
    logger.info(f"Analyze endpoint called for URL: {url}")

    try:
        # Process the URL completely
        result = await process_url(url)

        # Return the full analysis
        return AnalyzeResponse(
            url=url,
            og_metadata=result["og_metadata"],
            content={
                "full_text": result["text_content"],
                "summary": result["summary"]
            },
            cached=result["cached"]
        )
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest")
async def get_latest_articles() -> LatestArticlesResponse:
    logger.info("Latest articles endpoint called")
    try:
        latest = cache.get_latest_articles(limit=10)
        return LatestArticlesResponse(articles=latest)
    except Exception as e:
        logger.error(f"Error fetching latest articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preview/{encoded_url:path}", response_class=HTMLResponse)
async def preview_page(encoded_url: str):
    try:
        # Decode the URL and validate it
        url = unquote(encoded_url)
        
        # Fix URLs with single slash after scheme
        if url.startswith('http:/') and not url.startswith('http://'):
            url = url.replace('http:/', 'http://', 1)
        if url.startswith('https:/') and not url.startswith('https://'):
            url = url.replace('https:/', 'https://', 1)
        
        # Validate URL format
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid URL format: {url}"
            )
            
        # Ensure scheme is http or https
        if parsed.scheme not in ['http', 'https']:
            url = f"https://{parsed.netloc}{parsed.path}"
            if parsed.query:
                url += f"?{parsed.query}"
        
        # Process the URL to get metadata and content
        result = await process_url(url)
        
        og_metadata = result["og_metadata"]
        summary = result["summary"]

        # Create the redirect URL to read.html
        read_url = f"/read.html?url={html_escape(url)}"
        
        # Create HTML with proper Open Graph tags and escaped content
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{html_escape(og_metadata.get('title', 'Article Preview'))}</title>
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{html_escape(og_metadata.get('title', 'Article Preview'))}">
    <meta property="og:description" content="{html_escape(og_metadata.get('description', summary[:200] + '...' if len(summary) > 200 else summary))}">
    <meta property="og:image" content="{html_escape(og_metadata.get('image', ''))}">
    <meta property="og:url" content="{html_escape(url)}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="{html_escape(og_metadata.get('site_name', 'Smmryzr'))}">
    
    <!-- Redirect to read.html -->
    <meta http-equiv="refresh" content="0;url={read_url}">
</head>
<body>
    <p>Redirecting to summary...</p>
</body>
</html>"""
        
        return HTMLResponse(content=html)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating preview: {str(e)}"
        )

# Add this helper function at the top of the file with other imports
def html_escape(text):
    """Escape HTML special characters in text."""
    if not isinstance(text, str):
        text = str(text)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(
        ">", "&gt;").replace('"', "&quot;").replace("'", "&#039;")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
