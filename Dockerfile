# Simple test Dockerfile for RunPod
FROM python:3.11-slim

WORKDIR /app

# Install RunPod SDK
RUN pip install --no-cache-dir runpod>=1.6.0

# Copy handler
COPY handler.py .

# RunPod serverless entry point
CMD ["python", "-u", "handler.py"]
