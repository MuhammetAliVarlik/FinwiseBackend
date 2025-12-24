from fastapi.testclient import TestClient
from unittest.mock import patch
import pandas as pd
from datetime import datetime

def test_health_check(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_stock_not_found(client: TestClient):
    with patch("pandas_datareader.data.get_data_stooq") as mock_stooq:
        mock_stooq.return_value = pd.DataFrame()
        
        response = client.get("/stocks/INVALID")
        assert response.status_code == 404

def test_get_stock_success(client: TestClient):
    mock_df = pd.DataFrame(
        {'Close': [150.0], 'Volume': [10000]},
        index=[datetime.now()]
    )
    
    with patch("pandas_datareader.data.get_data_stooq") as mock_stooq:
        mock_stooq.return_value = mock_df
        
        response = client.get("/stocks/AAPL")
        
        if response.status_code != 200:
            print(f"DEBUG FAIL: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.0