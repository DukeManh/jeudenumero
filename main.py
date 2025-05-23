import random
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import edge_tts
import io
import logging

app = FastAPI()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

VOICES = [
    "fr-FR-DeniseNeural",
    "fr-CA-SylvieNeural",
    "fr-CA-AntoineNeural",
    "fr-FR-HenriNeural"
]

async def stream_audio(text: str):
    voix = random.choice(VOICES)
    logger.debug(f"Voix utilisée: {voix}")
    communicate = edge_tts.Communicate(text, voix)
    """audio chunks generator"""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}

@app.get("/tts")
async def tts(request: Request):
    client_ip = request.client.host
    logger.debug(f"Received request from IP: {client_ip}")

    text = request.query_params.get("text", "")
    if not text:
        logger.error("Missing text parameter")
        raise HTTPException(status_code=400, detail="Missing text")
    
    if len(text) > 200:
        logger.error("Text is too long")
        raise HTTPException(status_code=400, detail="Text is too long")
    try:
        logger.debug(f"Streaming audio for text: {text}")
        return StreamingResponse(
            stream_audio(text),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=output.mp3"}
        )
    except Exception as e:
        logger.exception(f"Error processing request: {str(e)}")
        raise
