import gradio as gr
import requests
import json

API_URL = "http://api:8000"

def extract_and_summarize(url: str, action: str):
    if not url:
        return "Please enter a URL"
        
    try:
        if action == "Extract Only":
            response = requests.post(f"{API_URL}/extract", json={"url": url})
            data = response.json()
            
            # Format the output
            metadata = json.dumps(data["og_metadata"], indent=2)
            return f"""## Metadata
```json
{metadata}
```

## Content
{data["text_content"]}"""

        elif action == "Summarize Only":
            # First extract
            extract_response = requests.post(f"{API_URL}/extract", json={"url": url})
            extract_data = extract_response.json()
            
            # Then summarize
            summary_response = requests.post(
                f"{API_URL}/summarize", 
                json={"text": extract_data["text_content"]}
            )
            summary_data = summary_response.json()
            
            return summary_data["summary"]
            
        else:  # Full Analysis
            response = requests.get(f"{API_URL}/analyze", params={"url": url})
            data = response.json()
            
            metadata = json.dumps(data["og_metadata"], indent=2)
            return f"""## Metadata
```json
{metadata}
```

## Summary
{data["content"]["summary"]}

## Full Content
{data["content"]["full_text"]}"""
            
    except Exception as e:
        return f"Error: {str(e)}"

# Create the interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # Article Analyzer
    Enter a URL to extract content, metadata, and get an AI-powered summary.
    """)
    
    with gr.Row():
        url_input = gr.Textbox(
            label="URL",
            placeholder="https://example.com/article",
            scale=4
        )
        action_input = gr.Radio(
            choices=["Full Analysis", "Extract Only", "Summarize Only"],
            value="Full Analysis",
            label="Action",
            scale=1
        )
    
    analyze_button = gr.Button("Analyze", variant="primary")
    output = gr.Markdown(label="Result")
    
    analyze_button.click(
        fn=extract_and_summarize,
        inputs=[url_input, action_input],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)