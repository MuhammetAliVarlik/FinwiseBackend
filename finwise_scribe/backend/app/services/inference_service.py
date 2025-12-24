import httpx
import os

class InferenceService:
    def __init__(self):
        # The internal docker networking URL
        self.scribe_url = os.getenv("SCRIBE_SERVICE_URL", "http://scribe:8001")

    async def predict_next_move(self, symbol: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.scribe_url}/predict",
                    json={"symbol": symbol},
                    timeout=60.0
                )
                if response.status_code != 200:
                    return {"error": f"Scribe Service Error: {response.text}"}
                return response.json()
            except Exception as e:
                return {"error": f"Gateway failed to reach Scribe Engine: {str(e)}"}

    async def chat(self, message: str, symbol: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.scribe_url}/chat",
                    json={"message": message, "symbol": symbol},
                    # INCREASED: 120.0 -> 300.0
                    timeout=300.0
                )
                if response.status_code != 200:
                    return {"error": f"Scribe Chat Error: {response.text}"}
                return response.json()
            except Exception as e:
                return {"error": f"Gateway Chat Error: {str(e)}"}