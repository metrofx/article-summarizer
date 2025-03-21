import gradio as gr
import requests
import json
import html
from urllib.parse import urlencode, parse_qs

API_URL = "http://api:8000"

def read_url_params():
    # Use context sharing instead of gr.get_state()
    try:
        from gradio.routes import Request
        request = Request.instance()
        query_params = request.query_params
        return query_params.get("url", [""])[0]
    except:
        return ""

def extract_and_summarize(url: str, theme_mode="light", state=None):
    if not url:
        return None, None, None

    try:
        # Always use the analyze endpoint for full processing
        response = requests.get(f"{API_URL}/analyze", params={"url": url})
        data = response.json()

        # Extract metadata for display
        og_metadata = data["og_metadata"]
        title = og_metadata.get("title", "No title available")
        description = og_metadata.get("description", "No description available")
        image = og_metadata.get("image", "")
        site_name = og_metadata.get("site_name", "")

        # Create metadata card HTML with theme-aware classes
        theme_class = "dark-mode" if theme_mode.lower() == "dark" else "light-mode"
        metadata_html = f"""
        <div class="metadata-card {theme_class}">
            <div class="metadata-content">
                <div class="metadata-text">
                    <h3>{html.escape(title)}</h3>
                    <p class="description">{html.escape(description)}</p>
                </div>
                <div class="metadata-footer">
                    {"<img src='" + image + "' alt='Article image'>" if image else ""}
                    <span class="site-name">{html.escape(site_name)}</span>
                </div>
            </div>
        </div>
        """

        # Prepare content
        summary = data["content"]["summary"] if "summary" in data["content"] else ""
        full_text = data["content"]["full_text"] if "full_text" in data["content"] else ""

        # Store URL in state if state is provided
        if state is not None:
            state.value = {"url": url}
        
        return metadata_html, summary, full_text

    except Exception as e:
        error_message = f"Error: {str(e)}"
        return f"<div class='error-card'>{error_message}</div>", "", ""

# Custom CSS with light/dark mode support and Medium-like font
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;1,300;1,400&display=swap');

/* Apply Merriweather font to everything */
body, .gradio-container, .gradio-container *, p, h1, h2, h3, h4, h5, h6, button, input, select, textarea {
    font-family: 'Merriweather', Georgia, serif !important;
}

/* Light mode variables */
body.light-mode {
    --bg-color: #ffffff;
    --text-color: #333333;
    --card-bg: #ffffff;
    --card-shadow: rgba(0,0,0,0.1);
    --accent-color: #4a6cf7;
    --secondary-bg: #f8f9ff;
    --border-color: #eaeaea;
    --error-bg: #fff0f0;
    --error-color: #e74c3c;
    --muted-text: #666666;
}

/* Dark mode variables */
body.dark-mode {
    --bg-color: #1a1a1a;
    --text-color: #f0f0f0;
    --card-bg: #2d2d2d;
    --card-shadow: rgba(0,0,0,0.3);
    --accent-color: #738aff;
    --secondary-bg: #252836;
    --border-color: #444444;
    --error-bg: #3d2525;
    --error-color: #ff6b6b;
    --muted-text: #bbbbbb;
}

/* Base styles that apply to both modes */
.container {
    max-width: 1000px;
    margin: 0 auto;
}

.metadata-card {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 20px;
    transition: transform 0.2s;
}

/* Add responsive layout for desktop */
@media (min-width: 768px) {
    .metadata-content {
        display: flex;
        gap: 20px;
        align-items: start;
    }
    
    .metadata-text {
        flex: 1;
    }
    
    .metadata-footer {
        flex: 0 0 200px;
        border-top: none;
        margin-top: 0;
        padding-top: 0;
        flex-direction: column;
    }
    
    .metadata-footer img {
        width: 200px;
        height: 150px;
        object-fit: cover;
        border-radius: 8px;
    }
}

.metadata-content {
    padding: 16px;
}

.metadata-content h3 {
    margin: 0 0 8px 0;
    color: var(--text-color);
    font-size: 16px;
    font-weight: 600;
    line-height: 1.4;
}

.description {
    color: var(--muted-text);
    font-size: 14px;
    line-height: 1.4;
    margin: 0 0 12px 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.metadata-footer {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
    border-top: 1px solid var(--border-color);
    padding-top: 12px;
}

.metadata-footer img {
    width: 40px;
    height: 40px;
    object-fit: cover;
    border-radius: 4px;
}

.site-name {
    color: var(--muted-text);
    font-size: 13px;
    font-weight: 500;
}

.content-container {
    background-color: var(--card-bg);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px var(--card-shadow);
    margin-bottom: 20px;
}

.summary-container {
    background-color: var(--secondary-bg);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px var(--card-shadow);
    border-left: 4px solid var(--accent-color);
}

.error-card {
    background-color: var(--error-bg);
    color: var(--error-color);
    padding: 16px;
    border-radius: 8px;
    border-left: 4px solid var(--error-color);
}

/* Medium-like article styling */
.article-content {
    font-size: 18px;
    line-height: 1.8;
    color: var(--text-color);
}

.article-summary {
    font-size: 18px;
    line-height: 1.8;
    color: var(--text-color);
}

/* Footer styling */
.footer {
    text-align: center;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color);
    color: var(--muted-text);
    font-size: 0.9em;
}

/* Improve tab styling */
.tab-nav button {
    font-weight: 400;
    font-size: 16px;
}

.tab-nav button.selected {
    font-weight: 700;
    color: var(--accent-color);
}

/* Improve button styling */
button.primary {
    background-color: var(--accent-color);
    color: white;
    font-weight: 700;
}
"""

# Create the interface
with gr.Blocks(css=custom_css) as demo:
    state = gr.State()
    
    # Set up theme handling
    def set_theme(theme):
        if theme == "Dark":
            return """
            <script>
                document.body.classList.remove('light-mode');
                document.body.classList.add('dark-mode');
            </script>
            """
        else:
            return """
            <script>
                document.body.classList.remove('dark-mode');
                document.body.classList.add('light-mode');
            </script>
            """

    # Initialize theme
    theme_html = gr.HTML("""
    <script>
        document.body.classList.add('light-mode');
    </script>
    """)

    gr.HTML("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="margin-bottom: 5px;">Article Analyzer</h1>
        <p style="color: var(--muted-text);">Extract content, metadata, and get AI-powered summaries from any article URL</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=4):
            url_input = gr.Textbox(
                label="Article URL",
                placeholder="https://example.com/article",
                show_label=False,
                value=read_url_params()  # Initialize with URL parameter if present
            )
            permalink = gr.HTML("", visible=False)  # Add permalink display
        with gr.Column(scale=1):
            analyze_button = gr.Button("Analyze", variant="primary")

    # Output components
    metadata_output = gr.HTML(label="Article Metadata")

    with gr.Tabs() as tabs:
        with gr.TabItem("Summary"):
            summary_output = gr.Markdown(label="AI Summary", elem_classes=["article-summary"])
        with gr.TabItem("Full Content"):
            content_output = gr.Markdown(label="Article Content", elem_classes=["article-content"])

    # Advanced Options at the bottom
    with gr.Accordion("Advanced Options", open=False):
        theme_toggle = gr.Radio(
            choices=["Light", "Dark"],
            value="Light",
            label="Theme Mode",
            interactive=True
        )

    # Handle theme toggle
    theme_toggle.change(
        fn=set_theme,
        inputs=theme_toggle,
        outputs=theme_html
    )

    def update_permalink(url):
        if url:
            try:
                from gradio.routes import Request
                request = Request.instance()
                # Get the base URL from the request
                base_url = str(request.base_url).rstrip('/')
                params = {"url": url}
                share_url = f"{base_url}?{urlencode(params)}"
                return gr.update(visible=True, value=f"""
                    <div style="margin-top: 10px;">
                        <span style="color: var(--muted-text);">Permalink: </span>
                        <a href="{share_url}" style="color: var(--accent-color);">{share_url}</a>
                    </div>
                """)
            except Exception as e:
                print(f"Error generating permalink: {e}")
                return gr.update(visible=False)
        return gr.update(visible=False)

    # Handle button click
    analyze_button.click(
        fn=extract_and_summarize,
        inputs=[url_input, theme_toggle, state],
        outputs=[metadata_output, summary_output, content_output]
    ).then(
        fn=update_permalink,
        inputs=[url_input],
        outputs=[permalink]
    )

    # Also analyze when pressing Enter in the URL field
    url_input.submit(
        fn=extract_and_summarize,
        inputs=[url_input, theme_toggle, state],
        outputs=[metadata_output, summary_output, content_output]
    ).then(
        fn=update_permalink,
        inputs=[url_input],
        outputs=[permalink]
    )

    # If there's a URL parameter, trigger analysis on load
    if read_url_params():
        demo.load(
            fn=extract_and_summarize,
            inputs=[url_input, theme_toggle, state],
            outputs=[metadata_output, summary_output, content_output]
        ).then(
            fn=update_permalink,
            inputs=[url_input],
            outputs=[permalink]
        )

    gr.HTML("""
    <div class="footer">
        <p>Article Analyzer © 2025</p>
    </div>
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)