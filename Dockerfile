FROM python:3.10-slim

# System deps for soundfile (libsndfile)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (backend-only, excludes heavy streamlit)
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt

# Copy application code
COPY . .

# Expose default port (Railway overrides via $PORT)
EXPOSE 8000

# Start uvicorn — Railway sets $PORT at runtime
# Use shell form so $PORT is expanded by the shell
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 120
