# Argonauts Backend Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies
# libpq-dev is needed for building psycopg2 if not using binary, but helpful to have.
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port (Cloud Run expects 8080 by default)
EXPOSE 8080

# Run the application using Gunicorn
# Workers: 1-2 is usually enough for a demo/small instance. 
# Threads: 8 allows handling multiple concurrent requests (good for I/O bound tasks like DB/API calls)
# Timeout: 0 is recommended for Cloud Run to let it handle timeouts
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 run:app






