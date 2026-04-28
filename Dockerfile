FROM python:3.10-slim

# System deps for soundfile (libsndfile)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default: start FastAPI backend
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
