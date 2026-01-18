# Coqui TTS Service for Inquiry Institute

High-quality Text-to-Speech using Coqui XTTS-v2, deployed on RunPod Serverless with T4 GPU.

## Features

- **XTTS-v2 Model**: State-of-the-art multilingual TTS
- **16+ Languages**: English, German, French, Italian, Spanish, and more
- **Voice Cloning**: Clone any voice from ~6 seconds of audio
- **Faculty Voices**: Pre-configured voices for Inquiry Institute faculty
- **Serverless**: Pay only for what you use, scales to zero

## Deployment to RunPod

### 1. Build and Push Docker Image

```bash
# Login to Docker Hub (or use RunPod's registry)
docker login

# Build the image
docker build -t yourusername/coqui-tts-runpod:latest .

# Push to registry
docker push yourusername/coqui-tts-runpod:latest
```

### 2. Create RunPod Serverless Endpoint

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Click "New Endpoint"
3. Configure:
   - **Container Image**: `yourusername/coqui-tts-runpod:latest`
   - **GPU Type**: T4 (16GB VRAM) - cheapest option that works
   - **Workers**: 
     - Min: 0 (scales to zero)
     - Max: 3 (or as needed)
   - **Idle Timeout**: 5 seconds
   - **Execution Timeout**: 300 seconds
4. Add Volume (optional, for custom voices):
   - Mount path: `/runpod-volume`
   - Size: 1GB
5. Click "Deploy"

### 3. Get Your Endpoint URL

After deployment, you'll get an endpoint URL like:
```
https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync
```

## API Usage

### Basic TTS Request

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "Hello, this is a test of the Coqui TTS system.",
      "language": "en"
    }
  }'
```

### Faculty Voice Request

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "The unexamined life is not worth living.",
      "faculty_slug": "a.plato",
      "language": "en"
    }
  }'
```

### Voice Cloning Request

```bash
# First, base64 encode your reference audio
SPEAKER_WAV=$(base64 -i reference_voice.wav)

curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": {
      \"text\": \"This will sound like the reference voice.\",
      \"speaker_wav_base64\": \"$SPEAKER_WAV\",
      \"language\": \"en\"
    }
  }"
```

### Response Format

```json
{
  "id": "request-id",
  "status": "COMPLETED",
  "output": {
    "audio_base64": "BASE64_ENCODED_WAV_AUDIO",
    "format": "wav",
    "duration_seconds": 3.5,
    "language": "en",
    "faculty_slug": "a.plato"
  }
}
```

## Supported Languages

XTTS-v2 supports these languages:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Polish (pl)
- Turkish (tr)
- Russian (ru)
- Dutch (nl)
- Czech (cs)
- Arabic (ar)
- Chinese (zh-cn)
- Japanese (ja)
- Hungarian (hu)
- Korean (ko)

## Faculty Voice Configuration

Faculty voices are configured in `handler.py`. To add custom voice samples:

1. Record 6-30 seconds of clear speech (WAV format, 22050Hz)
2. Upload to the RunPod volume at `/runpod-volume/faculty-voices/a.faculty_name.wav`
3. The handler will automatically use these files

## Pricing

RunPod Serverless T4 pricing (approximate):
- **Per-second billing**: ~$0.00031/sec when active
- **Idle**: $0 when scaled to zero
- **Cold start**: ~10-15 seconds (model loading)

For a typical 5-second TTS request:
- Active time: ~3-5 seconds
- Cost: ~$0.001-0.002 per request

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires GPU)
python handler.py
```

## Integration with Supabase

Update your Supabase Edge Function to call the RunPod endpoint:

```typescript
const RUNPOD_API_KEY = Deno.env.get('RUNPOD_API_KEY');
const RUNPOD_ENDPOINT = Deno.env.get('RUNPOD_TTS_ENDPOINT');

async function generateSpeech(text: string, facultySlug: string, language: string = 'en') {
  const response = await fetch(`${RUNPOD_ENDPOINT}/runsync`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${RUNPOD_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      input: {
        text,
        faculty_slug: facultySlug,
        language,
      }
    })
  });
  
  const result = await response.json();
  
  if (result.status === 'COMPLETED') {
    // Decode base64 audio
    const audioBytes = Uint8Array.from(atob(result.output.audio_base64), c => c.charCodeAt(0));
    return audioBytes;
  }
  
  throw new Error(result.error || 'TTS generation failed');
}
```
