# Lightweight TTS using edge-tts
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir runpod>=1.6.0 edge-tts

# Copy handler
COPY handler.py .

# RunPod entry point
CMD ["python", "-u", "handler.py"]
