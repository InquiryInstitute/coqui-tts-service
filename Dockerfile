# RunPod Serverless Coqui TTS
# Uses XTTS-v2 for high-quality multilingual TTS with voice cloning

FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY handler.py .

# Create cache directory for models
ENV COQUI_TOS_AGREED=1
ENV HF_HOME=/runpod-volume/huggingface
ENV TTS_HOME=/runpod-volume/tts

# Create directories
RUN mkdir -p /runpod-volume/faculty-voices /runpod-volume/huggingface /runpod-volume/tts

# RunPod serverless entry point
CMD ["python", "-u", "handler.py"]
