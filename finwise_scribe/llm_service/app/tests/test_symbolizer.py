import pytest
import pandas as pd
from app.ml.symbolizer import FinwiseSymbolizer

def test_symbolizer_initialization():
    """Verify the symbolizer initializes with correct defaults."""
    symbolizer = FinwiseSymbolizer(tickers=["AAPL"], period="1y")
    assert symbolizer.tickers == ["AAPL"]
    assert symbolizer.period == "1y"

def test_calculate_technicals(sample_market_data: pd.DataFrame):
    """Verify RSI, MACD, and Trends calculate correctly on 50+ rows."""
    symbolizer = FinwiseSymbolizer()
    indicators = symbolizer.calculate_technicals(sample_market_data)
    
    assert "RSI" in indicators
    assert "MACD_HIST" in indicators
    assert "TREND" in indicators
    assert indicators["TREND"] in ["BULLISH", "BEARISH"]

def test_process_generates_tokens(sample_market_data: pd.DataFrame):
    """Verify raw market data maps to P_ and V_ neuro-symbolic tokens."""
    symbolizer = FinwiseSymbolizer()
    
    data, indicators, tokens = symbolizer.process(sample_market_data)
    
    # 1 row is dropped due to pct_change()
    assert len(data) == len(sample_market_data) - 1
    assert len(tokens) == len(sample_market_data) - 1
    
    # Check that composite tokens were formed (e.g., 'P_HIGH_V_MID')
    assert isinstance(tokens.iloc[0], str)
    assert "P_" in tokens.iloc[0] and "V_" in tokens.iloc[0]