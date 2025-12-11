FROM tensorflow/tensorflow:2.15.0

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install remaining Python dependencies (TensorFlow already in base image)
# Remove tensorflow and keras from installation as they're in base image
RUN pip install --no-cache-dir --upgrade pip && \
    grep -v "^tensorflow" requirements.txt | grep -v "^keras" > requirements-temp.txt && \
    pip install --no-cache-dir -r requirements-temp.txt && \
    rm requirements-temp.txt

# Copy application code
COPY . .

# Create required directory structure for storage and ML models
# In GCP, we use /tmp/storage for temporary file handling
RUN mkdir -p /tmp/storage/images /tmp/storage/saliency_maps && \
    mkdir -p /tmp/ml_models && \
    chmod -R 777 /tmp/storage /tmp/ml_models

# Expose port (Cloud Run uses PORT env var, defaults to 8080)
EXPOSE 8080

# Run the application (production mode - no reload)
# Use PORT environment variable from Cloud Run, default to 8000 for local
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
