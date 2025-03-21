import gradio as gr
import requests
import json
import html

API_URL = "http://api:8000"

def extract_and_summarize(url: str, theme_mode="light"):
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
            <div class="metadata-image">
                {"<img src='" + image + "' alt='Article image'>" if image else "<div class='no-image'>No image available</div>"}
            </div>
            <div class="metadata-content">
                <h3>{html.escape(title)}</h3>
                <p class="site-name">{html.escape(site_name)}</p>
                <p class="description">{html.escape(description)}</p>
            </div>
        </div>
        """

        # Prepare content
        summary = data["content"]["summary"] if "summary" in data["content"] else ""
        full_text = data["content"]["full_text"] if "full_text" in data["content"] else ""

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
    display: flex;
    background-color: var(--card-bg);
    border-radius: 12px;
    box-shadow: 0 4px 12px var(--card-shadow);
    overflow: hidden;
    margin-bottom: 20px;
    transition: transform 0.2s;
}

.metadata-card:hover {
    transform: translateY(-3px);
}

.metadata-image {
    flex: 0 0 200px;
    background-color: #f5f5f5;
    display: flex;
    align-items: center;
    justify-content: center;
}

.metadata-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.no-image {
    color: var(--muted-text);
    text-align: center;
    padding: 20px;
}

.metadata-content {
    flex: 1;
    padding: 16px;
}

.metadata-content h3 {
    margin-top: 0;
    margin-bottom: 8px;
    color: var(--text-color);
    font-size: 18px;
    font-weight: 700;
}

.site-name {
    color: var(--accent-color);
    font-size: 14px;
    margin-bottom: 8px;
}

.description {
    color: var(--muted-text);
    font-size: 14px;
    line-height: 1.6;
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
                show_label=False
            )
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

    # Handle button click
    analyze_button.click(
        fn=extract_and_summarize,
        inputs=[url_input, theme_toggle],
        outputs=[metadata_output, summary_output, content_output]
    )

    # Also analyze when pressing Enter in the URL field
    url_input.submit(
        fn=extract_and_summarize,
        inputs=[url_input, theme_toggle],
        outputs=[metadata_output, summary_output, content_output]
    )

    gr.HTML("""
    <div class="footer">
        <p>Article Analyzer © 2025</p>
    </div>
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)