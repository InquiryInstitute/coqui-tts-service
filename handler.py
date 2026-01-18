"""
RunPod Serverless Handler for Coqui TTS
Supports XTTS-v2 with voice cloning and 16+ languages
"""

import runpod
import torch
import base64
import io
import os
import tempfile

# Global model reference (lazy loaded)
tts_model = None

def get_tts_model():
    """Lazy load the TTS model on first request"""
    global tts_model
    if tts_model is None:
        from TTS.api import TTS
        print("Loading XTTS-v2 model (this may take a few minutes on first run)...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        
        # Agree to terms
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("Model loaded successfully!")
    return tts_model


def handler(job):
    """
    RunPod serverless handler for TTS requests
    
    Input:
        text: str - Text to synthesize
        language: str (optional) - Language code (default: "en")
        speaker: str (optional) - Built-in speaker name
        speaker_wav_base64: str (optional) - Base64 WAV for voice cloning
        
    Output:
        audio_base64: str - Base64 encoded WAV audio
    """
    try:
        job_input = job.get("input", {})
        
        # Extract parameters
        text = job_input.get("text", "")
        language = job_input.get("language", "en")
        speaker = job_input.get("speaker", "Claribel Dervla")  # Default built-in speaker
        speaker_wav_base64 = job_input.get("speaker_wav_base64")
        
        if not text:
            return {"error": "Text is required"}
        
        if len(text) > 5000:
            return {"error": "Text too long (max 5000 characters)"}
        
        print(f"Generating TTS for: {text[:50]}...")
        
        # Get the TTS model
        tts = get_tts_model()
        
        # Generate audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_output:
            output_path = temp_output.name
        
        # Check if voice cloning with custom audio
        if speaker_wav_base64:
            # Decode and save reference audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_speaker:
                temp_speaker.write(base64.b64decode(speaker_wav_base64))
                speaker_wav_path = temp_speaker.name
            
            tts.tts_to_file(
                text=text,
                speaker_wav=speaker_wav_path,
                language=language,
                file_path=output_path
            )
            os.unlink(speaker_wav_path)
        else:
            # Use built-in speaker
            tts.tts_to_file(
                text=text,
                speaker=speaker,
                language=language,
                file_path=output_path
            )
        
        # Read and encode output
        with open(output_path, "rb") as f:
            audio_bytes = f.read()
        
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        os.unlink(output_path)
        
        print(f"Generated {len(audio_bytes)} bytes of audio")
        
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


# Start RunPod serverless worker
runpod.serverless.start({"handler": handler})
