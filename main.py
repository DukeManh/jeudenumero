# server.py
import random
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import edge_tts
import io
import logging
import os

app = FastAPI()

# Store last request times per IP
last_requests = {}

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

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
    client_ip = request.client.host
    logger.debug(f"Received request from IP: {client_ip}")
    
    current_time = time.time()
    if client_ip in last_requests:
        time_passed = current_time - last_requests[client_ip]
        logger.debug(f"Time since last request: {time_passed:.2f}s")
        if time_passed < 2:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait 2 seconds between calls."
            )
    
    last_requests[client_ip] = current_time
    
    try:
        text = request.query_params.get("text", "")
        if not text:
            logger.error("Missing text parameter")
            raise HTTPException(status_code=400, detail="Missing text")
        
        logger.debug(f"Generating audio for text: {text}")
        audio_buffer = await generate_audio(text)
        logger.debug("Audio generation successful")
        
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=output.mp3"}
        )
    except Exception as e:
        logger.exception(f"Error processing request: {str(e)}")
        raise

# port = int(os.environ.get("PORT", 8000))
# if __name__ == '__main__':
#     import uvicorn
#     logger.info(f"Starting server on port {port}")
#     uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
