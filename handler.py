"""
RunPod Serverless Handler for Coqui TTS
Simple version to debug connectivity
"""

import runpod

def handler(job):
    """Simple handler to test RunPod connectivity"""
    try:
        job_input = job.get("input", {})
        text = job_input.get("text", "No text provided")
        
        # Just echo back for now to verify connectivity
        return {
            "status": "success",
            "message": f"Received: {text}",
            "echo": text
        }
        
    except Exception as e:
        return {"error": str(e)}


# Start RunPod serverless worker
runpod.serverless.start({"handler": handler})
