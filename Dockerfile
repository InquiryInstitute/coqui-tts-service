# Clean Python base with Coqui TTS for RunPod
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install RunPod SDK first (before TTS to avoid conflicts)
RUN pip install --no-cache-dir runpod>=1.6.0

# Install Coqui TTS
RUN pip install --no-cache-dir TTS

# Copy handler
COPY handler.py .

# Agree to Coqui TOS
ENV COQUI_TOS_AGREED=1

# RunPod entry point
CMD ["python", "-u", "handler.py"]
