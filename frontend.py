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
        metadata_html = f"""
        <div class="metadata-card {theme_mode}-mode">
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
        return f"<div class='error-card {theme_mode}-mode'>{error_message}</div>", "", ""

# Custom CSS with light/dark mode support
custom_css = """
:root {
    --light-bg: #ffffff;
    --light-text: #333333;
    --light-card-bg: #ffffff;
    --light-card-shadow: rgba(0,0,0,0.1);
    --light-accent: #4a6cf7;
    --light-secondary-bg: #f8f9ff;
    --light-border: #eaeaea;
    --light-error-bg: #fff0f0;
    --light-error-color: #e74c3c;

    --dark-bg: #1a1a1a;
    --dark-text: #f0f0f0;
    --dark-card-bg: #2d2d2d;
    --dark-card-shadow: rgba(0,0,0,0.3);
    --dark-accent: #738aff;
    --dark-secondary-bg: #252836;
    --dark-border: #444444;
    --dark-error-bg: #3d2525;
    --dark-error-color: #ff6b6b;
}

body.dark-mode {
    background-color: var(--dark-bg);
    color: var(--dark-text);
}

.container {
    max-width: 1000px;
    margin: 0 auto;
}

/* Light mode styles */
.metadata-card.light-mode {
    display: flex;
    background-color: var(--light-card-bg);
    border-radius: 12px;
    box-shadow: 0 4px 12px var(--light-card-shadow);
    overflow: hidden;
    margin-bottom: 20px;
    transition: transform 0.2s;
}

.light-mode .metadata-content h3 {
    color: var(--light-text);
}

.light-mode .site-name {
    color: var(--light-accent);
}

.light-mode .description {
    color: #555;
}

.light-mode .content-container {
    background-color: var(--light-card-bg);
    box-shadow: 0 4px 12px var(--light-card-shadow);
}

.light-mode .summary-container {
    background-color: var(--light-secondary-bg);
    border-left: 4px solid var(--light-accent);
}

.light-mode .error-card {
    background-color: var(--light-error-bg);
    color: var(--light-error-color);
    border-left: 4px solid var(--light-error-color);
}

/* Dark mode styles */
.metadata-card.dark-mode {
    display: flex;
    background-color: var(--dark-card-bg);
    border-radius: 12px;
    box-shadow: 0 4px 12px var(--dark-card-shadow);
    overflow: hidden;
    margin-bottom: 20px;
    transition: transform 0.2s;
}

.dark-mode .metadata-content h3 {
    color: var(--dark-text);
}

.dark-mode .site-name {
    color: var(--dark-accent);
}

.dark-mode .description {
    color: #bbbbbb;
}

.dark-mode .content-container {
    background-color: var(--dark-card-bg);
    box-shadow: 0 4px 12px var(--dark-card-shadow);
}

.dark-mode .summary-container {
    background-color: var(--dark-secondary-bg);
    border-left: 4px solid var(--dark-accent);
}

.dark-mode .error-card {
    background-color: var(--dark-error-bg);
    color: var(--dark-error-color);
    border-left: 4px solid var(--dark-error-color);
}

/* Common styles */
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
    color: #888;
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
    font-size: 18px;
}

.site-name {
    font-size: 14px;
    margin-bottom: 8px;
}

.description {
    font-size: 14px;
    line-height: 1.5;
}

.content-container {
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}

.summary-container {
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.tab-nav {
    margin-bottom: 20px;
}

.error-card {
    padding: 16px;
    border-radius: 8px;
}

.theme-toggle {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    margin-bottom: 10px;
}

.theme-toggle label {
    margin-right: 10px;
}
"""

# Create the interface
with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    # State for theme mode
    theme_state = gr.State("light")

    gr.HTML("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="margin-bottom: 5px;">Article Analyzer</h1>
        <p style="color: #666;">Extract content, metadata, and get AI-powered summaries from any article URL</p>
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
            summary_output = gr.Markdown(label="AI Summary")
        with gr.TabItem("Full Content"):
            content_output = gr.Markdown(label="Article Content")

    # Advanced Options at the bottom
    with gr.Accordion("Advanced Options", open=False):
        theme_toggle = gr.Radio(
            choices=["Light", "Dark"],
            value="Light",
            label="Theme Mode",
            interactive=True
        )

    # Handle theme toggle
    def update_theme(choice):
        return "light" if choice == "Light" else "dark"

    theme_toggle.change(
        fn=update_theme,
        inputs=theme_toggle,
        outputs=theme_state
    )

    # Handle button click with theme awareness
    def analyze_with_theme(url, theme):
        return extract_and_summarize(url, theme)

    analyze_button.click(
        fn=analyze_with_theme,
        inputs=[url_input, theme_state],
        outputs=[metadata_output, summary_output, content_output]
    )

    # Also analyze when pressing Enter in the URL field
    url_input.submit(
        fn=analyze_with_theme,
        inputs=[url_input, theme_state],
        outputs=[metadata_output, summary_output, content_output]
    )

    gr.HTML("""
    <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #888; font-size: 0.9em;">Article Analyzer © 2025</p>
    </div>
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)