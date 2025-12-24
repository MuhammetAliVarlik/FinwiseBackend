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

        # 2. Construct Professional Prompt (Chain-of-Thought)
        prompt = (
            f"### SYSTEM ROLE\n"
            f"You are Finwise Scribe, an expert Financial Pattern Recognition Engine. "
            f"You analyze discretized market data where price action is converted into symbolic tokens:\n"
            f"- P_SURGE: Significant upward momentum.\n"
            f"- P_CRASH: Significant downward momentum.\n"
            f"- P_STABLE: Low volatility/consolidation.\n\n"
            f"### DATA CONTEXT\n"
            f"The following token sequence represents the last 60 trading days for {symbol}:\n"
            f"[{history_str}]\n\n"
            f"### TASK\n"
            f"Analyze the sequence for volatility clusters, regime changes, or fractal patterns. "
            f"Predict the single most likely NEXT state token.\n\n"
            f"### RESPONSE FORMAT\n"
            f"Prediction: [Token]\n"
            f"Reasoning: [2-3 sentences explaining the pattern identified]"
        )

        # 3. Call Ollama
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": "finwise_scribe_v1", # Ensuring we use your custom model
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2, # Lower temperature for precise predictions
                            "stop": ["###"]
                        }
                    },
                    timeout=300.0 # 5 Minute timeout for hardware buffer
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

    async def chat(self, message: str, symbol: str):
        """
        Handles conversational queries with market context injection.
        """
        # 1. Fetch Context
        context_str = ""
        try:
            symbolizer = FinwiseSymbolizer(tickers=[symbol])
            raw_df = symbolizer.fetch_data()
            if not raw_df.empty:
                _, _, tokens = symbolizer.process(raw_df)
                history = " ".join(tokens.tail(30).values)
                context_str = f"Last 30 Days of {symbol}: [{history}]"
        except Exception:
            context_str = "Market data unavailable."

        # 2. Construct Chat Prompt
        prompt = (
            f"System: You are Scribe, a professional financial AI assistant. "
            f"You speak concisely and professionally. "
            f"Base your answers on this symbolic market data: {context_str}\n"
            f"User: {message}\n"
            f"Scribe:"
        )

        # 3. Call Ollama
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": "finwise_scribe_v1", 
                        "prompt": prompt, 
                        "stream": False,
                        "options": {
                            "temperature": 0.7, # Higher temp for natural conversation
                            "stop": ["User:", "System:"]
                        }
                    },
                    timeout=500.0
                )
                response.raise_for_status()
                result = response.json()
                return {"response": result.get("response", "")}
            except Exception as e:
                return {"error": f"Chat inference failed: {str(e)}"}