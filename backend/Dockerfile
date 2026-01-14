# Use Python slim image with PyTorch CPU
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including those needed for bcrypt and cryptography)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    curl \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies (CPU-only torch for smaller image)
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.0+cpu \
    torchvision==0.16.0+cpu \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/profiles /app/data/global_calibration

# Set environment variables
ENV PORT=8080
ENV DATA_DIR=/app/data

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Run with uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
