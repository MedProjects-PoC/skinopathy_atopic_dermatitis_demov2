# Multi-stage build for optimized production image
# Stage 1: Build stage - compile dependencies
FROM tensorflow/tensorflow:2.15.0 AS builder

WORKDIR /build

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies with pip caching disabled
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    grep -v "^tensorflow" requirements.txt | grep -v "^keras" > requirements-filtered.txt && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements-filtered.txt && \
    rm requirements-filtered.txt

# Stage 2: Runtime stage - minimal production image
FROM tensorflow/tensorflow:2.15.0

WORKDIR /app

# Install only runtime system dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

# Copy pre-built wheels from builder
COPY --from=builder /build/wheels /wheels

# Install wheels (already built, no compilation needed)
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copy only necessary source files (uses .dockerignore)
COPY requirements.txt .
COPY app/ ./app/
COPY ml_models/ ./ml_models/

# Create required directory structure for runtime
RUN mkdir -p /tmp/storage/images /tmp/storage/saliency_maps /tmp/ml_models && \
    chmod -R 777 /tmp/storage /tmp/ml_models && \
    chmod -R 755 /app

# Non-root user for security (optional but recommended)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run application with explicit settings
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --access-log"]
