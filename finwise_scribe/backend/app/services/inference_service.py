import httpx
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

class InferenceService:
    def __init__(self):
        # Default to the internal docker alias
        self.scribe_url = os.getenv("SCRIBE_SERVICE_URL", "http://scribe:8001")
        
        # TIMEOUT CONFIGURATION
        # Connect: 5s (If Scribe is down, fail fast)
        # Read: 45s (Give Ollama time to load, but fail BEFORE the Frontend's 60s limit)
        self.timeout = httpx.Timeout(45.0, connect=5.0)

    async def predict_next_move(self, ticker: str):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"Sending prediction request for {ticker} to {self.scribe_url}")
                
                response = await client.post(
                    f"{self.scribe_url}/predict/{ticker}",
                    json={} 
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.ConnectError:
                logger.error("Failed to connect to Scribe Service")
                return {"error": "AI Engine Unreachable. Check if 'scribe' container is running."}
                
            except httpx.ReadTimeout:
                logger.warning("AI Engine timed out (likely Cold Start)")
                return {"error": "AI Model is warming up. Please try again in 30 seconds."}
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Scribe returned error: {e.response.text}")
                return {"error": f"AI Error: {e.response.status_code}"}
                
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                return {"error": f"System Error: {str(e)}"}

    async def chat(self, message: str, context: str):
        # Apply similar robustness to the Chat endpoint
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                payload = {"message": message, "context": context}
                response = await client.post(f"{self.scribe_url}/chat", json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Chat failed: {str(e)}")
                return {"response": "I'm having trouble thinking right now. Please try again."}