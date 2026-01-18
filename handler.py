"""
RunPod Serverless Handler for Coqui TTS
Supports XTTS-v2 with voice cloning and 16+ languages
Model downloads on first request and is cached in volume
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
        
        # Set environment for model caching
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("Model loaded successfully!")
    return tts_model

# Pre-defined faculty voice samples (will be loaded from volume)
FACULTY_VOICES_DIR = "/runpod-volume/faculty-voices"

# Default speaker samples for different voice types
DEFAULT_SPEAKERS = {
    "male_british": "default_male_british.wav",
    "female_british": "default_female_british.wav",
    "male_german": "default_male_german.wav",
    "female_french": "default_female_french.wav",
    "male_italian": "default_male_italian.wav",
}

# Faculty to voice mapping
FACULTY_CONFIG = {
    "a.plato": {"voice_type": "male_british", "language": "en"},
    "a.aristotle": {"voice_type": "male_british", "language": "en"},
    "a.socrates": {"voice_type": "male_british", "language": "en"},
    "a.hypatia": {"voice_type": "female_british", "language": "en"},
    "a.einstein": {"voice_type": "male_german", "language": "en"},
    "a.newton": {"voice_type": "male_british", "language": "en"},
    "a.curie": {"voice_type": "female_french", "language": "en"},
    "a.tesla": {"voice_type": "male_british", "language": "en"},
    "a.darwin": {"voice_type": "male_british", "language": "en"},
    "a.feynman": {"voice_type": "male_british", "language": "en"},
    "a.hawking": {"voice_type": "male_british", "language": "en"},
    "a.kant": {"voice_type": "male_german", "language": "en"},
    "a.nietzsche": {"voice_type": "male_german", "language": "de"},
    "a.shakespeare": {"voice_type": "male_british", "language": "en"},
    "a.davinci": {"voice_type": "male_italian", "language": "en"},
    "a.montessori": {"voice_type": "female_british", "language": "en"},
    "a.woolf": {"voice_type": "female_british", "language": "en"},
    "a.ada": {"voice_type": "female_british", "language": "en"},
}


def get_speaker_wav(faculty_slug: str = None, voice_type: str = None) -> str:
    """Get the speaker reference WAV file path"""
    # Check for faculty-specific voice file first
    if faculty_slug:
        faculty_voice_path = os.path.join(FACULTY_VOICES_DIR, f"{faculty_slug}.wav")
        if os.path.exists(faculty_voice_path):
            return faculty_voice_path
        
        # Use faculty config to get voice type
        if faculty_slug in FACULTY_CONFIG:
            voice_type = FACULTY_CONFIG[faculty_slug]["voice_type"]
    
    # Fall back to default voice type
    voice_type = voice_type or "male_british"
    default_voice = DEFAULT_SPEAKERS.get(voice_type, "default_male_british.wav")
    default_path = os.path.join(FACULTY_VOICES_DIR, default_voice)
    
    if os.path.exists(default_path):
        return default_path
    
    # If no voice files exist, return None
    return None


def handler(job):
    """
    RunPod serverless handler for TTS requests
    
    Input:
        text: str - Text to synthesize
        faculty_slug: str (optional) - Faculty identifier for voice selection
        language: str (optional) - Language code (default: "en")
        speaker_wav_base64: str (optional) - Base64 encoded reference audio for voice cloning
        
    Output:
        audio_base64: str - Base64 encoded WAV audio
        duration_seconds: float - Audio duration
    """
    job_input = job["input"]
    
    # Extract parameters
    text = job_input.get("text", "")
    faculty_slug = job_input.get("faculty_slug")
    language = job_input.get("language", "en")
    speaker_wav_base64 = job_input.get("speaker_wav_base64")
    output_format = job_input.get("format", "wav")
    
    if not text:
        return {"error": "Text is required"}
    
    if len(text) > 5000:
        return {"error": "Text too long (max 5000 characters)"}
    
    try:
        # Get the TTS model (lazy loaded)
        tts = get_tts_model()
        
        # Determine speaker reference
        speaker_wav_path = None
        temp_speaker_file = None
        
        # If base64 speaker audio provided, decode it
        if speaker_wav_base64:
            temp_speaker_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_speaker_file.write(base64.b64decode(speaker_wav_base64))
            temp_speaker_file.close()
            speaker_wav_path = temp_speaker_file.name
        else:
            # Get from faculty config or defaults
            speaker_wav_path = get_speaker_wav(faculty_slug)
        
        # Get language from faculty config if not specified
        if faculty_slug and faculty_slug in FACULTY_CONFIG:
            language = job_input.get("language") or FACULTY_CONFIG[faculty_slug].get("language", "en")
        
        # If no speaker reference, we need one for XTTS
        if not speaker_wav_path or not os.path.exists(speaker_wav_path):
            return {
                "error": "No speaker reference available. Please provide speaker_wav_base64 or upload voice samples to the volume.",
                "hint": "Upload a 6-30 second WAV file to /runpod-volume/faculty-voices/{faculty_slug}.wav"
            }
        
        # Generate audio
        with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as temp_output:
            output_path = temp_output.name
        
        # Use voice cloning with reference audio
        tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav_path,
            language=language,
            file_path=output_path
        )
        
        # Read output and encode
        with open(output_path, "rb") as f:
            audio_bytes = f.read()
        
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # Calculate approximate duration
        duration_seconds = len(audio_bytes) / (22050 * 2)  # XTTS outputs 22050Hz
        
        # Cleanup temp files
        if temp_speaker_file:
            os.unlink(temp_speaker_file.name)
        os.unlink(output_path)
        
        return {
            "audio_base64": audio_base64,
            "format": output_format,
            "duration_seconds": round(duration_seconds, 2),
            "language": language,
            "faculty_slug": faculty_slug
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# For local testing
if __name__ == "__main__":
    # Test the handler locally
    test_job = {
        "input": {
            "text": "Hello, this is a test of the Coqui TTS system.",
            "language": "en"
        }
    }
    result = handler(test_job)
    print(result)
else:
    # RunPod serverless entry point
    runpod.serverless.start({"handler": handler})
