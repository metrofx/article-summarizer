from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from bs4 import BeautifulSoup
import requests
import trafilatura
import os
from dotenv import load_dotenv
from typing import Optional
import json

# Load environment variables
load_dotenv()

app = FastAPI()

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class URLInput(BaseModel):
    url: HttpUrl

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
        text = trafilatura.extract(downloaded, include_links=True, output_format='markdown')
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

    prompt = f"""Summarize article text surrounded by <content> </content> tags into structured key ideas, making it easy to read and comprehend. Respond with the language of the article. The summary should be concise, clear, and capture the main points of the content. Start the response directly with the content, without any preamble or introductory statements. End with important quote taken from the article that is unique and capture attention.
<content>
{text}
</content>
"""

    data = {
        "model": "nousresearch/hermes-3-llama-3.1-70b",  # Replace with a valid model name
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

@app.get("/analyze")
async def analyze_url(url: str):
    try:
        # Validate URL
        url_input = URLInput(url=url)

        # Extract OpenGraph metadata
        og_metadata = extract_opengraph_metadata(url)

        # Extract text content
        text_content = extract_text_content(url)

        # Generate summary
        summary = await summarize_text(text_content)

        # Prepare response
        response = {
            "url": url,
            "og_metadata": og_metadata,
            "content": {
                "full_text": text_content,
                "summary": summary
            }
        }

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
