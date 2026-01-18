# RunPod Serverless Coqui TTS
# Uses pre-built Coqui TTS image with XTTS support

FROM ghcr.io/coqui-ai/tts:latest

WORKDIR /app

# Install RunPod SDK
RUN pip install --no-cache-dir runpod>=1.6.0

# Copy handler
COPY handler.py .

# Environment for model caching
ENV COQUI_TOS_AGREED=1
ENV HF_HOME=/runpod-volume/huggingface
ENV TTS_HOME=/runpod-volume/tts

# Create directories
RUN mkdir -p /runpod-volume/faculty-voices /runpod-volume/huggingface /runpod-volume/tts

# RunPod serverless entry point
CMD ["python", "-u", "handler.py"]
