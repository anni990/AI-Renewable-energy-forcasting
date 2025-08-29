# Create a simplified Dockerfile for testing
FROM python:3.10-slim

WORKDIR /app

# Install minimal dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and modify to exclude pyodbc temporarily
COPY requirements.txt .
RUN grep -v "pyodbc" requirements.txt > requirements_simple.txt && \
    pip install --no-cache-dir -r requirements_simple.txt

# Copy application
COPY . .

# Create logs directory
RUN mkdir -p /app/logs


# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]