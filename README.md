# Smmryzr - Article Summarizer

Smmryzr is a web application that extracts content, metadata, and generates AI-powered summaries from any URL. It provides a clean interface for users to input URLs and receive structured summaries and full content extraction.

## Features

- **Content Extraction**: Extract full text content from web pages
- **Metadata Extraction**: Retrieve OpenGraph metadata (title, description, image, etc.)
- **AI Summarization**: Generate concise summaries using AI
- **Caching**: Cache results for faster subsequent access
- **Responsive UI**: Clean, responsive interface with light/dark mode support
- **API Integration**: Built with FastAPI for backend and Alpine.js for frontend
- **Docker Support**: Easy deployment using Docker and Docker Compose

## Tech Stack

- **Backend**: Python, FastAPI, DuckDB
- **Frontend**: HTML, CSS, JavaScript (Alpine.js)
- **AI**: OpenRouter API
- **Database**: DuckDB for caching
- **Deployment**: Docker, Nginx

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/metrofx/article-summarizer.git
   cd article-summarizer
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenRouter API key
   ```

3. Build and run with Docker:
   ```bash
   docker-compose up --build
   ```

4. Access the application at `http://localhost:7860`

## API Endpoints

- `POST /extract` - Extract content and metadata
- `POST /summarize` - Generate summary from text or URL
- `GET /analyze` - Full analysis of a URL
- `GET /latest` - Get latest processed articles
- `GET /preview/{url}` - Generate preview page with OpenGraph tags

## Configuration

Environment variables in `.env`:

- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `ALLOWED_IPS` - Comma-separated list of allowed IP ranges

## Development

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the FastAPI server:
   ```bash
   uvicorn api.main:app --reload
   ```

3. Run the frontend development server:
   ```bash
   cd web
   python -m http.server 8000
   ```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License

## Support

If you find this project useful, consider supporting the developer:
[Donate via Saweria](https://saweria.co/xfortem)
