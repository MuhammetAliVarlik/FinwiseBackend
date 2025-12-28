import pytest
from httpx import AsyncClient
from unittest.mock import patch
import pandas as pd
from datetime import datetime

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_get_stock_not_found(client: AsyncClient):
    # We patch the same location. Even though it's run in a thread, 
    # the patch works because it replaces the function object in the module.
    with patch("pandas_datareader.data.get_data_stooq") as mock_stooq:
        mock_stooq.return_value = pd.DataFrame()
        
        response = await client.get("/stocks/INVALID")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_stock_success(client: AsyncClient):
    mock_df = pd.DataFrame(
        {'Close': [150.0], 'Volume': [10000]},
        index=[datetime.now()]
    )
    
    with patch("pandas_datareader.data.get_data_stooq") as mock_stooq:
        mock_stooq.return_value = mock_df
        
        response = await client.get("/stocks/AAPL")
        
        if response.status_code != 200:
            print(f"DEBUG FAIL: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.0