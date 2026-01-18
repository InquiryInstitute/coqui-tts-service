# RunPod Serverless Coqui TTS
# Uses XTTS-v2 for high-quality multilingual TTS with voice cloning

FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the XTTS-v2 model during build (faster cold starts)
RUN python -c "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2')"

# Copy handler
COPY handler.py .

# Create directory for faculty voices (will be mounted from volume)
RUN mkdir -p /runpod-volume/faculty-voices

# RunPod serverless entry point
CMD ["python", "-u", "handler.py"]
