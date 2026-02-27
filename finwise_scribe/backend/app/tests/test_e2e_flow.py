import pytest
import httpx
import os

# Read the backend URL from environment or default to the Docker exposed port
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

@pytest.mark.asyncio
async def test_full_neuro_symbolic_pipeline():
    """
    E2E Test: 
    1. Triggers the backend forecast route.
    2. Backend fetches data.
    3. Backend calls LLM Service.
    4. Validates the final aggregated response.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Simulate a user requesting a forecast for Bitcoin
        payload = {"ticker": "BTC-USD", "days_history": 30}
        
        response = await client.post("/api/v1/forecast/generate", json=payload, timeout=60.0)
        
        # If the backend is wired correctly to the LLM service via Docker network
        assert response.status_code == 200, f"Failed with {response.text}"
        
        data = response.json()
        assert "ticker" in data
        assert data["ticker"] == "BTC-USD"
        assert "forecast" in data
        assert "confidence_score" in data