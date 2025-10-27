# app/tests/test_stocks.py

def test_get_stock(client):
    symbol = "AAPL"
    response = client.get(f"/stocks/{symbol}")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "symbol" in data
        assert data["symbol"] == symbol
