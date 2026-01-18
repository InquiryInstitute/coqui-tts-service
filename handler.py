"""
RunPod Serverless Handler for Coqui TTS
Supports XTTS-v2 with voice cloning and 16+ languages
"""

import runpod
import base64
import os
import tempfile

# Global model reference (lazy loaded)
tts_model = None

def get_tts_model():
    """Lazy load the TTS model on first request"""
    global tts_model
    if tts_model is None:
        import torch
        from TTS.api import TTS
        
        # Use faster VITS model instead of XTTS
        print("Loading VITS model...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        
        os.environ["COQUI_TOS_AGREED"] = "1"
        # VITS is much smaller and faster to load
        tts_model = TTS("tts_models/en/ljspeech/vits").to(device)
        print("Model loaded!")
    return tts_model


def handler(job):
    """TTS handler"""
    try:
        job_input = job.get("input", {})
        text = job_input.get("text", "")
        language = job_input.get("language", "en")
        speaker = job_input.get("speaker", "Claribel Dervla")
        
        if not text:
            return {"error": "Text is required"}
        
        if len(text) > 5000:
            return {"error": "Text too long (max 5000 characters)"}
        
        print(f"Generating TTS: {text[:50]}...")
        
        tts = get_tts_model()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name
        
        # VITS is single-speaker, no speaker/language params needed
        tts.tts_to_file(
            text=text,
            file_path=output_path
        )
        
        with open(output_path, "rb") as f:
            audio_bytes = f.read()
        
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        os.unlink(output_path)
        
        print(f"Generated {len(audio_bytes)} bytes")
        
        return {
            "audio_base64": audio_base64,
            "format": "wav",
            "language": language
        }
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        return {"error": str(e)}


runpod.serverless.start({"handler": handler})
