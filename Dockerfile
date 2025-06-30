# Use Python 3.11 slim image for better performance and smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/env/secrets/marketa-459704-64f65195b184.json

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm for MCP tools (required for perplexity-mcp)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install uv for Python package management (needed for uvx command)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


RUN git clone https://github.com/ppl-ai/modelcontextprotocol.git
RUN cd modelcontextprotocol/perplexity-ask && npm install



# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# COPY .env .
# COPY marketa-459704-64f65195b184.json .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create necessary directories
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with uvicorn
CMD ["uvicorn", "creatoros.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 