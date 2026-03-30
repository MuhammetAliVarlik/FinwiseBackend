import pytest
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

# Import your FastAPI app
from app.main import app 

@pytest.fixture
def client() -> TestClient:
    """Provides a FastAPI TestClient for the LLM Service."""
    return TestClient(app)

@pytest.fixture
def sample_market_data() -> pd.DataFrame:
    """Provides 60 days of sample OHLCV data."""
    dates = pd.date_range(start='2023-01-01', periods=60, freq='D')
    data = {
        'Open': np.linspace(100, 150, 60),
        'High': np.linspace(105, 155, 60),
        'Low': np.linspace(95, 145, 60),
        'Close': np.linspace(102, 152, 60),
        'Volume': np.random.randint(1000, 5000, size=60)
    }
    return pd.DataFrame(data, index=dates)