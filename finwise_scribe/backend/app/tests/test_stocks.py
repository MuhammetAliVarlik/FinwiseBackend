import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_get_stock_not_found(client: AsyncClient):
    # Patch 'asyncio.to_thread' directly in the service module
    # This prevents ANY thread from starting and ANY network call from happening
    with patch("app.services.stock_service.asyncio.to_thread") as mock_thread:
        # Simulate Stooq returning empty DataFrame (Not Found)
        mock_thread.return_value = pd.DataFrame()
        
        response = await client.get("/stocks/INVALID")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_stock_success(client: AsyncClient):
    mock_df = pd.DataFrame(
        {'Close': [150.0], 'Volume': [10000], 'Open': [145.0], 'High': [155.0], 'Low': [140.0]},
        index=[datetime.now()]
    )
    
    # Patch 'asyncio.to_thread' directly
    with patch("app.services.stock_service.asyncio.to_thread") as mock_thread:
        mock_thread.return_value = mock_df
        
        response = await client.get("/stocks/AAPL")
        
        if response.status_code != 200:
            print(f"DEBUG FAIL: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.0