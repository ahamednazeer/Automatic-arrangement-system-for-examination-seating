# Use Python 3.11 slim base (multi-arch: works on amd64 & arm64)
FROM --platform=$BUILDPLATFORM python:3.11-slim

# Prevent Python from writing pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# System dependencies (for building Python wheels, DB drivers, SSL, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       default-libmysqlclient-dev \
       libffi-dev \
       libssl-dev \
       curl \
       netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Ensure runtime directories exist
RUN mkdir -p uploads

# Expose the application port
EXPOSE 5000

# Run with Flask’s dev server (for debugging, shows logs)
# In production, switch back to Gunicorn.
CMD ["python", "-u", "app.py"]

