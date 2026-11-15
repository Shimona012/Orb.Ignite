#SI
# Base image with Python 3.11 slim
FROM python:3.11-slim

# Prevent Python from writing .pyc and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Install system dependencies (build-essential for compiling any wheel if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy repository files
COPY . .

# Expose standard Cloud Run port
EXPOSE 8080

# Healthcheck for container stability
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Launch Streamlit app on port 8080
ENTRYPOINT ["streamlit", "run", "Pages/Dashboard.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=true"]
