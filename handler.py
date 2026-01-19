"""
RunPod Serverless Handler for TTS
Uses edge-tts via subprocess for reliable sync operation
"""

import runpod
import base64
import subprocess
import tempfile
import os


def handler(job):
    """TTS handler using edge-tts CLI"""
    try:
        job_input = job.get("input", {})
        text = job_input.get("text", "")
        voice = job_input.get("voice", "en-GB-RyanNeural")
        
        if not text:
            return {"error": "Text is required"}
        
        if len(text) > 5000:
            return {"error": "Text too long (max 5000 characters)"}
        
        print(f"Generating TTS: '{text[:50]}...' with voice {voice}")
        
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            output_path = f.name
        
        # Run edge-tts via subprocess
        cmd = ["edge-tts", "--voice", voice, "--text", text, "--write-media", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return {"error": f"edge-tts failed: {result.stderr}"}
        
        # Read the audio file
        with open(output_path, "rb") as f:
            audio_bytes = f.read()
        
        os.unlink(output_path)
        
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        print(f"Generated {len(audio_bytes)} bytes of audio")
        
        return {
            "audio_base64": audio_base64,
            "format": "mp3",
            "voice": voice,
            "length": len(audio_bytes)
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "TTS generation timed out"}
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        return {"error": str(e)}


runpod.serverless.start({"handler": handler})
