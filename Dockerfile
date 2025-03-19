FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for lxml and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "lxml[html_clean]"

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Command will be overridden by docker-compose for web service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]