"""
RunPod Serverless Handler for TTS
Uses edge-tts for fast, lightweight TTS
"""

import runpod
import base64
import tempfile
import asyncio

async def generate_tts(text, voice="en-GB-RyanNeural"):
    """Generate TTS using edge-tts"""
    import edge_tts
    
    communicate = edge_tts.Communicate(text, voice)
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        output_path = f.name
    
    await communicate.save(output_path)
    
    with open(output_path, "rb") as f:
        audio_bytes = f.read()
    
    import os
    os.unlink(output_path)
    
    return audio_bytes


def handler(job):
    """TTS handler using edge-tts"""
    try:
        job_input = job.get("input", {})
        text = job_input.get("text", "")
        voice = job_input.get("voice", "en-GB-RyanNeural")
        
        if not text:
            return {"error": "Text is required"}
        
        if len(text) > 5000:
            return {"error": "Text too long (max 5000 characters)"}
        
        print(f"Generating TTS: {text[:50]}... with voice {voice}")
        
        audio_bytes = asyncio.run(generate_tts(text, voice))
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        print(f"Generated {len(audio_bytes)} bytes")
        
        return {
            "audio_base64": audio_base64,
            "format": "mp3",
            "voice": voice
        }
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        return {"error": str(e)}


runpod.serverless.start({"handler": handler})
