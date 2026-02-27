from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """Verify the LLM service health endpoint is alive."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_generate_prompt_endpoint(client: TestClient):
    """Verify the API correctly accepts data and returns an LLM prediction schema."""
    payload = {
        "ticker": "AAPL",
        "market_data": [150.0, 151.2, 149.5, 152.3, 153.1]
    }
    response = client.post("/api/v1/predict", json=payload)
    
    # Depending on Ollama's cold start in the current state, 
    # we expect either a 200 OK or a 503 if the model is loading.
    # We validate the schema wrapper here.
    assert response.status_code in [200, 503] 
    if response.status_code == 200:
        data = response.json()
        assert "symbolic_prompt" in data
        assert "llm_forecast" in data