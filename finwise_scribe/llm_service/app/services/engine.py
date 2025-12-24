import httpx
from app.core.config import settings
from app.ml.symbolizer import FinwiseSymbolizer

class ScribeEngine:
    async def predict(self, symbol: str):
        # 1. Symbolize Data
        try:
            symbolizer = FinwiseSymbolizer(tickers=[symbol])
            raw_df = symbolizer.fetch_data()
            if raw_df.empty:
                return {"error": f"No market data found for {symbol}"}
                
            _, _, tokens = symbolizer.process(raw_df)
            history_str = " ".join(tokens.tail(60).values) # Last 60 days
        except Exception as e:
            return {"error": f"Symbolization failed: {str(e)}"}

        # 2. Construct Prompt
        prompt = (
            f"Analyze the following financial token sequence for {symbol}: {history_str}. "
            "Predict the next token and explain why."
        )

        # 3. Call Ollama (The Hardware Layer)
        async with httpx.AsyncClient() as client:
            try:
                # We use 'llama3' or the custom tag you load into Ollama
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": "llama3", 
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "symbol": symbol,
                    "prediction": result.get("response", ""),
                    "history_used": "60 Days (Symbolized)"
                }
            except Exception as e:
                return {"error": f"Ollama Inference failed: {str(e)}"}