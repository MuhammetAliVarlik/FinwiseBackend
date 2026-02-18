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

    async def _run_llm(self, prompt: str, temperature: float = 0.2) -> dict:
        """
        Helper to execute inference on the Ollama Container.
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
            symbolizer = FinwiseSymbolizer(tickers=[symbol], period="1y")
            raw_df = symbolizer.fetch_data()
            
            if raw_df.empty: 
                return {"error": f"No market data found for {symbol}"}
                
            # [CRITICAL UPDATE]: Capture 'indicators' from the middle return value
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

        # --- STEP 4: Construct Neuro-Symbolic Prompt ---
        # [UPDATED]: Now includes INDICATORS section
        prompt = (
            f"### SYSTEM ROLE\n"
            f"You are Finwise Scribe, a Financial Reasoning Engine. "
            f"Synthesize Technical Trends with Real-Time News.\n\n"
            f"### DATA STREAMS\n"
            f"1. PRICE TOKENS (60d History): [{future_history}]\n"
            f"2. INDICATORS (Math): RSI={rsi_str} | Trend={trend_str}\n"  # <-- NEW
            f"3. NEURO (Real-Time News): {news_context}\n\n"
            f"### REASONING TASKS\n"
            f"1. Check Indicators: Is RSI OVERBOUGHT (>70) or OVERSOLD (<30)?\n"
            f"2. Scan News: Are there catalysts (Earnings, Regulation, Hacks)?\n"
            f"3. CONFLICT RESOLUTION: If Price is STABLE but News is CATASTROPHIC, "
            f"predict P_CRASH.\n\n"
            f"### OUTPUT FORMAT (JSON Only)\n"
            f"{{\n"
            f"  \"symbol\": \"{symbol}\",\n"
            f"  \"prediction\": \"P_[ACTION]_V_[VOLATILITY]\",\n"
            f"  \"confidence\": 0.0 to 1.0,\n"
            f"  \"reasoning\": \"Concise explanation citing specific news or patterns.\",\n"
            f"  \"divergence_reasoning\": \"Explain why you disagreed with the trend (if applicable), else null.\"\n"
            f"}}"
        )
        
        # --- STEP 5: Execute Inference ---
        llm_result = await self._run_llm(prompt)
        
        # --- STEP 6: Validate & Parse (Pydantic) ---
        try:
            validated = PredictionResponse(**llm_result)
            final_pred = validated.prediction
            confidence = validated.confidence
            reasoning = validated.reasoning
            divergence_note = validated.divergence_reasoning
        except Exception as e:
            logger.warning(f"Schema Validation Failed: {e}. Using Safe Fallback.")
            final_pred = "P_STABLE_V_MID"
            confidence = 0.0
            reasoning = "Unable to generate structured reasoning."
            divergence_note = None

        # --- STEP 7: Detect Divergence ---
        is_divergent = (lstm_token != final_pred)
        divergence_type = "NONE"
        
        if is_divergent:
            if "CRASH" in final_pred and "CRASH" not in lstm_token:
                divergence_type = "RISK_ALERT" 
            elif "SURGE" in final_pred and "SURGE" not in lstm_token:
                divergence_type = "OPPORTUNITY_ALERT" 
            else:
                divergence_type = "DIRECTIONAL_MISMATCH"

        # --- STEP 8: Log Experiment (MLflow) ---
        try:
            with mlflow.start_run():
                mlflow.log_param("symbol", symbol)
                mlflow.log_metric("confidence", confidence)
                mlflow.log_metric("is_divergent", 1 if is_divergent else 0)
                mlflow.log_param("divergence_type", divergence_type)
                
                mlflow.log_text(news_context, "news_context.txt")
                mlflow.log_text(json.dumps(llm_result), "llm_output.json")
                mlflow.log_metric("latency", time.time() - start_time)
        except Exception as e:
            logger.warning(f"MLflow Logging Failed: {e}")

        return {
            "symbol": symbol,
            "prediction": final_pred,
            "confidence": confidence,
            "reasoning": reasoning,
            "shadow_baseline": lstm_future, 
            "divergence": divergence_type   
        }

    async def chat(self, message: str, symbol: str) -> Dict[str, str]:
        # 1. Gather Context
        try:
            symbolizer = FinwiseSymbolizer(tickers=[symbol])
            raw_df = symbolizer.fetch_data()
            _, indicators, tokens = symbolizer.process(raw_df) # Unpack indicators here too
            
            price_context = " ".join(tokens.tail(30).values)
            rsi_info = f"RSI: {indicators.get('RSI', 'N/A')}" # Add to chat context
        except:
            price_context = "Price data unavailable."
            rsi_info = ""

        news_context = await self.rag.retrieve_context(symbol)

        # 2. Chat Prompt
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

        result = await self._run_llm(prompt, temperature=0.7)
        return {"response": result.get("reasoning") or result.get("prediction") or "I processed your request but could not generate a text response."}