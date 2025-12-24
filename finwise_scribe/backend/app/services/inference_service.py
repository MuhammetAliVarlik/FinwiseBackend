import httpx
import os

class InferenceService:
    def __init__(self):
        # The internal docker networking URL defined in docker-compose
        self.scribe_url = os.getenv("SCRIBE_SERVICE_URL", "http://scribe:8001")

    async def predict_next_move(self, symbol: str):
        """
        Proxies the request to the dedicated LLM Microservice.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.scribe_url}/predict",
                    json={"symbol": symbol},
                    timeout=40.0
                )
                if response.status_code != 200:
                    return {"error": f"Scribe Service Error: {response.text}"}
                
                return response.json()
                
            except Exception as e:
                return {"error": f"Gateway failed to reach Scribe Engine: {str(e)}"}