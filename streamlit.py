import streamlit as st
import requests
import json
from urllib.parse import quote

def fetch_article_data(url):
    encoded_url = quote(url)
    api_endpoint = f"http://localhost:8000/analyze?url={encoded_url}"
    try:
        response = requests.get(api_endpoint)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="Article Analyzer", layout="wide")

    # URL input
    url = st.text_input("Enter article URL:")
    analyze_button = st.button("Analyze", type="primary")

    if url and analyze_button:
        data = fetch_article_data(url)

        if data:
            metadata = data['og_metadata']
            st.header(metadata['title'])

            # Source information
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