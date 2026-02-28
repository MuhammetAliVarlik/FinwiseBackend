import httpx
import mlflow
import time
import os
import json
import logging
import pandas as pd
from typing import Dict, Any

# Project Imports
from app.core.config import settings
from app.ml.symbolizer import FinwiseSymbolizer
from app.ml.lstm_engine import LSTMEngine
from app.services.context_service import ContextRetrievalService
from app.schemas.prompt import PredictionResponse

# Configure Structured Logging (Loki-ready)
logger = logging.getLogger("scribe.engine")

class ScribeEngine:
    def __init__(self):
        """
        The Neuro-Symbolic Core.
        Orchestrates the LSTM (Math), RAG (News), and LLM (Reasoning).
        """
        self.lstm = LSTMEngine()
        self.rag = ContextRetrievalService() # The "Neuro" Component (RSS)
        
        # Initialize MLflow for Shadow Mode Experiments
        self._setup_mlflow()

    def _setup_mlflow(self):
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        mlflow.set_tracking_uri(mlflow_uri)
        try:
            mlflow.set_experiment("Finwise_RealTime_NeuroSymbolic")
        except Exception as e:
            logger.warning(f"MLflow Setup Warning: {e}")

    async def _run_llm_token_only(self, prompt: str, temperature: float = 0.0) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": "finwise_scribe_v1", 
                        "prompt": prompt,
                        "stream": False,
                        "raw": True,
                        "options": {
                            "temperature": 0.0, 
                            "top_k": 1,
                            "num_ctx": 1024,
                            "stop": ["\n", " ", "<|end_of_text|>"]
                        }
                    },
                    timeout=300.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ollama Error {response.status_code}: {response.text}")
                    return "P_4_V_4"

                raw_text = response.json().get("response", "").strip()
                return raw_text.split(" ")[0] if raw_text else "P_4_V_4"

            except Exception as e:
                logger.error(f"LLM Token Inference Failed: {e}")
                return "P_4_V_4"

    async def _run_llm(self, prompt: str, temperature: float = 0.2) -> dict:
        """
        [KEPT INTACT] Standard helper to execute JSON inference on the Ollama Container.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": "finwise_scribe_v1", 
                        "prompt": prompt,
                        "stream": False,
                        "format": "json", 
                        "options": {
                            "temperature": temperature, 
                            "num_ctx": 4096 
                        }
                    },
                    timeout=300.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ollama Error {response.status_code}: {response.text}")
                    return {}

                raw_json = response.json().get("response", "{}")
                clean_json = raw_json.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)

            except json.JSONDecodeError:
                logger.error("Failed to parse LLM JSON output.")
                return {}
            except Exception as e:
                logger.error(f"LLM Inference Failed: {e}")
                return {}

    async def predict(self, symbol: str) -> Dict[str, Any]:
        """
        Main Neuro-Symbolic Inference Pipeline.
        """
        start_time = time.time()
        
        # --- STEP 1: Fetch Symbolic Data (Price & Indicators) ---
        try:
            symbolizer = FinwiseSymbolizer(tickers=[symbol], period="10y") # Changed to 10y for data depth
            raw_df = symbolizer.fetch_data()
            
            if raw_df.empty: 
                return {"error": f"No market data found for {symbol}"}
                
            # Capture 'indicators' from the middle return value
            _, indicators, full_tokens = symbolizer.process(raw_df)
            
            future_history = " ".join(full_tokens.tail(60).values)
            
            # Format Indicators for Prompt
            rsi_str = f"{indicators.get('RSI', 'N/A')} ({indicators.get('RSI_SIGNAL', 'N/A')})"
            trend_str = indicators.get('TREND', 'N/A')
            
        except Exception as e:
            logger.error(f"Symbolizer Failed: {e}")
            return {"error": "Technical Analysis failed."}

        # --- STEP 2: Fetch Neuro Context (Real-Time News) ---
        news_context = await self.rag.retrieve_context(symbol)
        
        # --- STEP 3: Run LSTM Baseline (The Control Group) ---
        lstm_future = self.lstm.predict(symbol, data_override=raw_df)
        lstm_token = lstm_future.get("prediction_token", "N/A")

        # --- STEP 4 & 5: [MODIFIED] Two-Step Execution to support the fine-tuned GGUF ---
        # 4a. Get the exact sequence token using the exact format you trained the model on
        sequence_prompt = (
            f"Predict the next market token for {symbol} based on history:\n"
            f"{future_history}\n"
            f"Response: "
        )
        predicted_token = await self._run_llm_token_only(sequence_prompt)

        # 4b. Map the 10x10 token to a Direction
        # P_0 to P_3 = BEARISH, P_4 to P_5 = NEUTRAL, P_6 to P_9 = BULLISH
        try:
            p_level = int(predicted_token.split('_')[1])
        except:
            p_level = 4
            
        if p_level >= 6:
            final_pred = "P_SURGE_V_HIGH" if p_level > 7 else "P_HIGH_V_MID"
            confidence = (p_level / 9) # Scales confidence based on decile
        elif p_level <= 3:
            final_pred = "P_CRASH_V_HIGH" if p_level < 2 else "P_LOW_V_MID"
            confidence = 1.0 - (p_level / 3)
        else:
            final_pred = "P_STABLE_V_MID"
            confidence = 0.5

        # 4c. Construct Synthetic Reasoning (Since GGUF only outputs tokens)
        signal_text = "bullish" if p_level >= 6 else ("bearish" if p_level <= 3 else "stable")
        reasoning = (
            f"Sequence model predicts a {signal_text} shift (Token: {predicted_token}). "
            f"Technical indicators show RSI at {indicators.get('RSI')} ({indicators.get('RSI_SIGNAL')}) "
            f"with a {indicators.get('TREND')} trend."
        )

        divergence_note = None

        # --- STEP 7: Detect Divergence [KEPT INTACT] ---
        is_divergent = (lstm_token != final_pred)
        divergence_type = "NONE"
        
        if is_divergent:
            if "CRASH" in final_pred and "CRASH" not in lstm_token:
                divergence_type = "RISK_ALERT" 
                divergence_note = "Model detected risk despite LSTM neutrality."
            elif "SURGE" in final_pred and "SURGE" not in lstm_token:
                divergence_type = "OPPORTUNITY_ALERT" 
                divergence_note = "Model detected opportunity despite LSTM neutrality."
            else:
                divergence_type = "DIRECTIONAL_MISMATCH"

        # --- STEP 8: MLOPS & SHADOW MODE TRACKING (ENRICHED) ---
        try:
            with mlflow.start_run():
                # 1. Base Prediction Metrics
                mlflow.log_param("symbol", symbol)
                mlflow.log_param("slm_prediction", final_pred)
                mlflow.log_metric("slm_confidence", confidence)
                mlflow.log_param("slm_raw_token", predicted_token)
                
                # 2. LSTM Baseline Metrics
                mlflow.log_param("lstm_token", lstm_token)
                mlflow.log_metric("lstm_p_change", lstm_future.get("predicted_change_pct", 0.0))
                mlflow.log_metric("lstm_v_change", lstm_future.get("predicted_vol_change", 0.0))
                
                # 3. Technical Indicators
                mlflow.log_metric("market_rsi", indicators.get("RSI", 0.0))
                mlflow.log_param("market_rsi_signal", indicators.get("RSI_SIGNAL", "UNKNOWN"))
                mlflow.log_param("market_trend", indicators.get("TREND", "UNKNOWN"))

                # 4. Divergence Analysis
                mlflow.log_metric("is_divergent", 1 if is_divergent else 0)
                mlflow.log_param("divergence_type", divergence_type)
                if divergence_note:
                    mlflow.log_param("divergence_note", divergence_note)
                
                # 5. DEBUG
                mlflow.log_text(sequence_prompt, "debug_exact_prompt.txt") 
                mlflow.log_text(news_context, "context_news.txt")
                
                mlflow.log_metric("latency_seconds", time.time() - start_time)
        except Exception as e:
            logger.warning(f"MLflow Logging Failed: {e}")

        # Returns exact dictionary structure expected by your UI/App
        return {
            "symbol": symbol,
            "prediction": final_pred,
            "confidence": confidence,
            "reasoning": reasoning,
            "shadow_baseline": lstm_future, 
            "divergence": divergence_type   
        }

    async def chat(self, message: str, symbol: str) -> Dict[str, str]:
        # 1. Gather Context [KEPT INTACT]
        try:
            symbolizer = FinwiseSymbolizer(tickers=[symbol])
            raw_df = symbolizer.fetch_data()
            _, indicators, tokens = symbolizer.process(raw_df) 
            
            price_context = " ".join(tokens.tail(30).values)
            rsi_info = f"RSI: {indicators.get('RSI', 'N/A')}" 
        except:
            price_context = "Price data unavailable."
            rsi_info = ""

        news_context = await self.rag.retrieve_context(symbol)

        # 2. Chat Prompt [KEPT INTACT]
        prompt = (
            f"### SYSTEM ROLE\n"
            f"You are Scribe, an expert financial analyst assistant.\n"
            f"### CONTEXT\n"
            f"Market Patterns (30d): [{price_context}]\n"
            f"Technical Indicators: {rsi_info}\n"
            f"Breaking News: {news_context}\n\n"
            f"### USER QUESTION\n"
            f"{message}\n\n"
            f"### RESPONSE\n"
            f"Answer the user concisely. Cite the news or patterns if relevant to their question."
        )

        # Uses the standard format="json" runner
        result = await self._run_llm(prompt, temperature=0.7)
        return {"response": result.get("reasoning") or result.get("prediction") or "I processed your request but could not generate a text response."}