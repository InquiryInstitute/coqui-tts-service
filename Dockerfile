# Clean Python base with Coqui TTS for RunPod
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install RunPod SDK first
RUN pip install --no-cache-dir runpod>=1.6.0

# Install Coqui TTS
RUN pip install --no-cache-dir TTS

# Pre-download the VITS model during build
ENV COQUI_TOS_AGREED=1
RUN python -c "from TTS.api import TTS; TTS('tts_models/en/ljspeech/vits')"

# Copy handler
COPY handler.py .

# RunPod entry point
CMD ["python", "-u", "handler.py"]
