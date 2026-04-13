# Multi-arch base image: works on Mac (arm64) and Windows/Linux (amd64)
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

EXPOSE 8080

ENTRYPOINT ["python", "/app/entrypoint.py"]
