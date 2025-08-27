# Multi-stage build for better reliability
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft repository and ODBC driver
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc \
    && rm -rf /var/lib/apt/lists/*

# Copy Microsoft ODBC driver from builder stage
COPY --from=builder /opt/microsoft /opt/microsoft
COPY --from=builder /usr/share/keyrings/microsoft-prod.gpg /usr/share/keyrings/
COPY --from=builder /etc/apt/sources.list.d/mssql-release.list /etc/apt/sources.list.d/

# Install ODBC driver in production stage
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]