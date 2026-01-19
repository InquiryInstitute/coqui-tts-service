"""
RunPod Serverless Handler for TTS
Uses edge-tts with faculty-specific voice mappings
"""

import runpod
import base64
import subprocess
import tempfile
import os

# Faculty voice mappings - authentic accents where possible
FACULTY_VOICES = {
    # Ancient Greek
    "a.plato": "el-GR-NestorasNeural",       # Greek male
    "a.aristotle": "el-GR-NestorasNeural",   # Greek male
    "a.socrates": "el-GR-NestorasNeural",    # Greek male
    "a.hypatia": "el-GR-AthinaNeural",       # Greek female
    
    # Scientists
    "a.einstein": "de-DE-ConradNeural",      # German male
    "a.newton": "en-GB-RyanNeural",          # British male
    "a.curie": "fr-FR-DeniseNeural",         # French female
    "a.tesla": "hr-HR-SreckoNeural",         # Croatian male (Serbian heritage)
    "a.darwin": "en-GB-RyanNeural",          # British male
    "a.feynman": "en-US-GuyNeural",          # American male
    "a.hawking": "en-GB-RyanNeural",         # British male
    "a.galileo": "it-IT-DiegoNeural",        # Italian male
    
    # Philosophers
    "a.kant": "de-DE-ConradNeural",          # German male
    "a.nietzsche": "de-DE-ConradNeural",     # German male
    "a.sartre": "fr-FR-HenriNeural",         # French male
    "a.foucault": "fr-FR-HenriNeural",       # French male
    "a.descartes": "fr-FR-HenriNeural",      # French male
    
    # Writers
    "a.shakespeare": "en-GB-RyanNeural",     # British male
    "a.woolf": "en-GB-SoniaNeural",          # British female
    "a.dickens": "en-GB-RyanNeural",         # British male
    "a.joyce": "en-IE-ConnorNeural",         # Irish male
    "a.borges": "es-AR-TomasNeural",         # Argentine male
    "a.maryshelley": "en-GB-SoniaNeural",    # British female
    "a.thoreau": "en-US-GuyNeural",          # American male
    "a.morrison": "en-US-JennyNeural",       # American female
    
    # Artists
    "a.davinci": "it-IT-DiegoNeural",        # Italian male
    "a.michelangelo": "it-IT-DiegoNeural",   # Italian male
    "a.picasso": "es-ES-AlvaroNeural",       # Spanish male
    "a.kahlo": "es-MX-DaliaNeural",          # Mexican female
    
    # Computer Scientists
    "a.turing": "en-GB-RyanNeural",          # British male
    "a.ada": "en-GB-SoniaNeural",            # British female (Lovelace)
    "a.hopper": "en-US-JennyNeural",         # American female
    "a.dijkstra": "nl-NL-MaartenNeural",     # Dutch male
    "a.knuth": "en-US-GuyNeural",            # American male
    
    # Mathematicians
    "a.ramanujan": "en-IN-PrabhatNeural",    # Indian male
    "a.euler": "de-CH-JanNeural",            # Swiss German male
    "a.gauss": "de-DE-ConradNeural",         # German male
    
    # Economists
    "a.smith": "en-GB-RyanNeural",           # Scottish/British male
    "a.keynes": "en-GB-RyanNeural",          # British male
    "a.sen": "en-IN-PrabhatNeural",          # Indian male
    
    # Eastern Thinkers
    "a.confucius": "zh-CN-YunxiNeural",      # Chinese male
    "a.suntzu": "zh-CN-YunxiNeural",         # Chinese male
    "a.tagore": "en-IN-PrabhatNeural",       # Indian male (Bengali)
    
    # Islamic Golden Age
    "a.ibnsina": "ar-SA-HamedNeural",        # Arabic male (Avicenna)
    "a.ibnkhaldun": "ar-SA-HamedNeural",     # Arabic male
    
    # Others
    "a.sorjuana": "es-MX-DaliaNeural",       # Mexican female
    "a.montessori": "it-IT-ElsaNeural",      # Italian female
    "a.steiner": "de-AT-JonasNeural",        # Austrian male
}

# Default voices by gender
DEFAULT_MALE = "en-GB-RyanNeural"
DEFAULT_FEMALE = "en-GB-SoniaNeural"


def get_voice(faculty_slug=None, voice=None):
    """Get appropriate voice for faculty or use provided voice"""
    if voice:
        return voice
    if faculty_slug and faculty_slug in FACULTY_VOICES:
        return FACULTY_VOICES[faculty_slug]
    return DEFAULT_MALE


def handler(job):
    """TTS handler with faculty voice support"""
    try:
        job_input = job.get("input", {})
        text = job_input.get("text", "")
        voice = job_input.get("voice")
        faculty_slug = job_input.get("faculty_slug")
        
        if not text:
            return {"error": "Text is required"}
        
        if len(text) > 5000:
            return {"error": "Text too long (max 5000 characters)"}
        
        # Get appropriate voice
        selected_voice = get_voice(faculty_slug, voice)
        
        print(f"TTS: '{text[:50]}...' voice={selected_voice} faculty={faculty_slug}")
        
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            output_path = f.name
        
        # Run edge-tts via subprocess
        cmd = ["edge-tts", "--voice", selected_voice, "--text", text, "--write-media", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return {"error": f"edge-tts failed: {result.stderr}"}
        
        # Read the audio file
        with open(output_path, "rb") as f:
            audio_bytes = f.read()
        
        os.unlink(output_path)
        
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        print(f"Generated {len(audio_bytes)} bytes")
        
        return {
            "audio_base64": audio_base64,
            "format": "mp3",
            "voice": selected_voice,
            "faculty_slug": faculty_slug,
            "length": len(audio_bytes)
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "TTS generation timed out"}
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        return {"error": str(e)}


# Expose voice list endpoint
def get_voices():
    """Return available faculty voices"""
    return {
        "faculty_voices": FACULTY_VOICES,
        "default_male": DEFAULT_MALE,
        "default_female": DEFAULT_FEMALE
    }


runpod.serverless.start({"handler": handler})
