# server.py
import random
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import edge_tts
import io

app = FastAPI()

# Store last request times per IP
last_requests = {}

async def generate_audio(text: str) -> io.BytesIO:
    """Génère l'audio (au format MPEG) pour le texte donné en utilisant edge_tts."""
    audio_buffer = io.BytesIO()
    les_voix = ["fr-FR-DeniseNeural", "fr-CA-SylvieNeural", "fr-CA-AntoineNeural", "fr-FR-HenriNeural"]
    voix = les_voix[random.randint(0, len(les_voix) - 1)]
    print(f"Voix utilisée: {voix}")
    communicate = edge_tts.Communicate(text, voix)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
    audio_buffer.seek(0)
    return audio_buffer

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}

@app.get("/tts") 
async def tts(request: Request):
    # Get client IP
    client_ip = request.client.host
    
    # Check rate limit
    current_time = time.time()
    if client_ip in last_requests:
        time_passed = current_time - last_requests[client_ip]
        if time_passed < 2:
            raise HTTPException(
                status_code=429, 
                detail="Too many requests. Please wait 2 seconds between calls."
            )
    
    # Update last request time
    last_requests[client_ip] = current_time
    
    text = request.query_params.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Missing text")
        
    audio_buffer = await generate_audio(text)
    return StreamingResponse(
        audio_buffer,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=output.mp3"}
    )


# if __name__ == '__main__':
#     import os
#     port = int(os.environ.get("PORT", 8000))
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=port)
