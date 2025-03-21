from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from bs4 import BeautifulSoup
import requests
import trafilatura
import os
from dotenv import load_dotenv
from typing import Optional
import json
from db import Cache
import logging

# Load environment variables
load_dotenv()

app = FastAPI()
cache = Cache()

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
            'include_formatting': False,
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

    prompt = f"""Summarize article text surrounded by <content> </content> tags into structured key ideas, making it easy to read and comprehend. If you detect non English content, respond with Bahasa Indonesia. The summary should be concise, clear, and capture the main points of the content. Start the response directly with the content, without any preamble or introductory statements. End with important quote taken from the article that is unique and capture attention.
<content>
{text}
</content>
"""

    data = {
        "model": "openai/gpt-4o-mini",  # Replace with a valid model name
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

@app.post("/extract")
async def extract_url_content(url_input: URLInput) -> ExtractResponse:
    url = str(url_input.url)
    logger.info(f"Extracting content from URL: {url}")
    
    try:
        # Check cache first
        cached_data = cache.get_cached_article(url)
        if cached_data:
            logger.info(f"Returning cached data for: {url}")
            return ExtractResponse(
                url=url,
                og_metadata=cached_data["og_metadata"],
                text_content=cached_data["text_content"],
                cached=True
            )
    except Exception as cache_error:
        logger.error(f"Cache error: {str(cache_error)}")

    try:
        og_metadata = extract_opengraph_metadata(url)
        text_content = extract_text_content(url)
        
        # Try to cache the results
        try:
            cache.cache_article(url, text_content, None, og_metadata)
        except Exception as cache_error:
            logger.error(f"Failed to cache results: {str(cache_error)}")

        return ExtractResponse(
            url=url,
            og_metadata=og_metadata,
            text_content=text_content
        )

    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize")
async def summarize_content(request: SummarizeRequest) -> SummarizeResponse:
    logger.info("Summarizing text content")
    
    try:
        # Check cache if URL is provided
        if request.url:
            cached_data = cache.get_cached_article(request.url)
            if cached_data and cached_data.get("summary"):
                logger.info(f"Returning cached summary for: {request.url}")
                return SummarizeResponse(summary=cached_data["summary"])

        summary = await summarize_text(request.text)
        
        # Cache the summary if URL is provided
        if request.url:
            try:
                # Get existing cached data first
                existing_data = cache.get_cached_article(request.url) or {}
                
                # Update cache with summary while preserving other data
                cache.cache_article(
                    url=request.url,
                    text_content=existing_data.get("text_content"),
                    summary=summary,
                    og_metadata=existing_data.get("og_metadata")
                )
                logger.info(f"Successfully cached summary for: {request.url}")
            except Exception as cache_error:
                logger.error(f"Failed to cache summary: {str(cache_error)}")
        
        return SummarizeResponse(summary=summary)
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze")
async def analyze_url(url: str):
    try:
        # Validate URL
        url_input = URLInput(url=url)
        logger.info(f"Analyzing URL: {url}")
        
        # First extract content
        extract_result = await extract_url_content(url_input)
        
        # Then summarize (now passing the URL)
        if not extract_result.text_content:
            raise HTTPException(status_code=422, detail="No content extracted to summarize")
            
        summarize_result = await summarize_content(SummarizeRequest(
            text=extract_result.text_content,
            url=url
        ))
        
        return {
            "url": url,
            "og_metadata": extract_result.og_metadata,
            "content": {
                "full_text": extract_result.text_content,
                "summary": summarize_result.summary
            },
            "cached": extract_result.cached
        }

    except HTTPException as http_error:
        logger.error(f"HTTP error: {str(http_error)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
