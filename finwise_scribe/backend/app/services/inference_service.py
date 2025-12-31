import httpx
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

class InferenceService:
    def __init__(self):
        # Default to the internal docker alias
        self.scribe_url = os.getenv("SCRIBE_SERVICE_URL", "http://scribe:8001")
        
        # Timeout: 45s to allow for Cold Starts, but fail before Frontend's 60s limit
        self.timeout = httpx.Timeout(45.0, connect=5.0)

    async def predict_next_move(self, ticker: str):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # FIX 1: Send to /predict (no ID in URL) and pass symbol in JSON body
                url = f"{self.scribe_url}/predict"
                payload = {"symbol": ticker}
                
                logger.info(f"Sending prediction request to {url} with payload {payload}")
                
                response = await client.post(url, json=payload)
                
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
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.scribe_url}/chat"
                
                # FIX 2: Changed key from 'context' to 'symbol' to match Scribe's ChatRequest schema
                payload = {
                    "message": message, 
                    "symbol": context
                }
                
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                logger.error(f"Chat failed: {str(e)}")
                return {"response": "I'm having trouble thinking right now. Please try again."}