# Coqui TTS for RunPod Serverless
FROM ghcr.io/coqui-ai/tts:latest

WORKDIR /app

# Install RunPod SDK
RUN pip install --no-cache-dir runpod>=1.6.0

# Copy handler
COPY handler.py .

# Agree to Coqui TOS
ENV COQUI_TOS_AGREED=1

# RunPod entry point
CMD ["python", "-u", "handler.py"]
