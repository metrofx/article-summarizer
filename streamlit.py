import streamlit as st
import requests
import json
from urllib.parse import quote, unquote

def fetch_article_data(url):
    # First decode the URL in case it's already URL-encoded
    decoded_url = unquote(url)
    # Then properly encode it for the API request
    encoded_url = quote(decoded_url, safe=':/?=')
    api_endpoint = f"http://api:8000/analyze?url={encoded_url}"
    try:
        response = requests.get(api_endpoint)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="Article Analyzer", layout="wide")

    # Get URL parameter if it exists
    query_params = st.query_params
    url_param = query_params.get("url", "")
    # Handle single value or list
    url_param = url_param[0] if isinstance(url_param, list) else url_param

    # Create two columns for URL input and Analyze button
    col1, col2 = st.columns([6, 1])  # 6:1 ratio for URL field:button

    # URL input and button in the same row
    with col1:
        url = st.text_input(" ", 
                           value=url_param,  # Set initial value from URL parameter
                           placeholder="Enter article URL:", 
                           label_visibility="collapsed")
    with col2:
        analyze_button = st.button("Analyze", type="primary")

    # Automatically analyze if URL parameter is present
    should_analyze = analyze_button or (url_param and not analyze_button)

    if url and should_analyze:
        data = fetch_article_data(url)

        if data:
            # Safely handle og_metadata
            metadata = data.get('og_metadata', {})
            if metadata.get('title'):
                st.header(metadata['title'])
            
            # Only show source if site_name exists
            if metadata.get('site_name'):
                st.write(f"**Source:** {metadata['site_name']}")

            # Display summary
            st.header("Summary")
            summary_text = data['content']['summary']
            
            # Split the summary into sections based on numbered points
            sections = summary_text.split('\n\n')
            
            # Display each section with proper formatting
            for section in sections:
                section = section.strip()
                if section:
                    if section[0].isdigit():
                        st.markdown(f"• {section[2:].strip()}")
                    else:
                        st.markdown(section)

            # Display full article in expander
            with st.expander("Show Full Article"):
                st.write(data['content']['full_text'])

if __name__ == "__main__":
    main()