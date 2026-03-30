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
from app.core.label_contract import (
    normalize_direction_label,
    normalize_prediction_token,
    signal_to_token,
)
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
                            "temperature": temperature,
                            "top_k": 1,
                            "num_ctx": settings.OLLAMA_NUM_CTX,
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
                            "num_ctx": settings.OLLAMA_NUM_CTX,
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

    async def _run_llm_text(self, prompt: str, temperature: float = 0.4) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": "finwise_scribe_v1",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_ctx": settings.OLLAMA_NUM_CTX,
                        },
                    },
                    timeout=300.0,
                )

                if response.status_code != 200:
                    logger.error(f"Ollama Error {response.status_code}: {response.text}")
                    return ""

                return response.json().get("response", "").strip()
            except Exception as e:
                logger.error(f"LLM Text Inference Failed: {e}")
                return ""

    async def predict(self, symbol: str, context_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
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
                
            # Capture indicators + symbolic sequence from the symbolizer.
            _, indicators, full_tokens = symbolizer.process(raw_df)
            future_history = " ".join(full_tokens.tail(30).values)
            
        except Exception as e:
            logger.error(f"Symbolizer Failed: {e}")
            return {"error": "Technical Analysis failed."}

        # Prefer explicit backend technical context when available.
        if context_data and isinstance(context_data, dict):
            normalized_context = {
                "RSI": context_data.get("rsi", indicators.get("RSI")),
                "RSI_SIGNAL": context_data.get("rsi_signal", indicators.get("RSI_SIGNAL")),
                "TREND": context_data.get("trend", indicators.get("TREND")),
                "MACD_HIST": context_data.get("macd_hist", indicators.get("MACD_HIST")),
                "PRICE": context_data.get("price", indicators.get("PRICE")),
                "INDICATOR_TOKENS": context_data.get("indicator_tokens", indicators.get("INDICATOR_TOKENS", [])),
            }
            indicators.update({k: v for k, v in normalized_context.items() if v is not None})

        indicator_tokens = indicators.get("INDICATOR_TOKENS", [])
        if not indicator_tokens:
            indicator_tokens = [
                f"TREND_{indicators.get('TREND', 'NEUTRAL')}",
                "RSI_HIGH" if (indicators.get("RSI") or 50) > 70 else ("RSI_LOW" if (indicators.get("RSI") or 50) < 30 else "RSI_NEUTRAL"),
                "MACD_BULLISH" if (indicators.get("MACD_HIST") or 0) >= 0 else "MACD_BEARISH",
            ]

        # --- STEP 2: Fetch Neuro Context (Real-Time News) ---
        news_context = await self.rag.retrieve_context(symbol)
        
        # --- STEP 3: Run LSTM Baseline (The Control Group) ---
        lstm_future = self.lstm.predict(symbol, data_override=raw_df)
        lstm_token = lstm_future.get("prediction_token", "N/A")

        # --- STEP 4: Reasoning Prompt over Symbolized Technical Context ---
        prompt = (
            "### SYSTEM ROLE\n"
            "You are Finwise Scribe, a disciplined financial reasoning engine.\n"
            "Use the symbolized technical context to infer direction; do not guess raw prices.\n"
            "Reason step-by-step internally, then return ONLY valid JSON with this schema:\n"
            "{\"symbol\": string, \"signal\": \"BULLISH\"|\"BEARISH\"|\"NEUTRAL\", \"confidence\": 0-100 integer, \"reasoning\": string, \"divergence_reasoning\": string|null}.\n"
            "\n"
            "### CONTEXT\n"
            f"Symbol: {symbol}\n"
            f"Indicator Tokens: {', '.join(indicator_tokens)}\n"
            f"Technical Snapshot: RSI={indicators.get('RSI')}, RSI_SIGNAL={indicators.get('RSI_SIGNAL')}, TREND={indicators.get('TREND')}, MACD_HIST={indicators.get('MACD_HIST')}\n"
            f"Sequence Tokens (latest): {future_history}\n"
            f"News Context: {news_context}\n"
            "\n"
            "### TASK\n"
            "Synthesize a directional signal and confidence from the technical + token context."
        )

        llm_result = await self._run_llm(prompt, temperature=0.1)

        # Robust fallback if JSON generation fails.
        fallback_signal = "BULLISH" if indicators.get("TREND") == "BULLISH" else ("BEARISH" if indicators.get("TREND") == "BEARISH" else "NEUTRAL")
        if not llm_result:
            llm_result = {
                "symbol": symbol,
                "signal": fallback_signal,
                "confidence": 60,
                "reasoning": (
                    f"Fallback synthesis: RSI={indicators.get('RSI')} ({indicators.get('RSI_SIGNAL')}), "
                    f"trend={indicators.get('TREND')}, MACD_HIST={indicators.get('MACD_HIST')}."
                ),
                "divergence_reasoning": None,
            }

        try:
            parsed = PredictionResponse.model_validate(llm_result)
        except Exception:
            parsed = PredictionResponse(
                symbol=symbol,
                signal=fallback_signal,
                confidence=60,
                reasoning=(
                    f"Fallback synthesis: RSI={indicators.get('RSI')} ({indicators.get('RSI_SIGNAL')}), "
                    f"trend={indicators.get('TREND')}, MACD_HIST={indicators.get('MACD_HIST')}."
                ),
                divergence_reasoning=None,
            )

        canonical_signal = normalize_direction_label(parsed.signal)
        final_pred = signal_to_token(canonical_signal)
        confidence = round(parsed.confidence / 100.0, 3)
        reasoning = parsed.reasoning

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
                mlflow.log_param("slm_label", canonical_signal)
                mlflow.log_metric("slm_confidence", confidence)
                mlflow.log_param("slm_signal", canonical_signal)
                
                # 2. LSTM Baseline Metrics
                mlflow.log_param("lstm_token", lstm_token)
                mlflow.log_param("lstm_label", normalize_prediction_token(lstm_token, n_quantiles=symbolizer.n_quantiles))
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
                mlflow.log_text(prompt, "debug_reasoning_prompt.txt") 
                mlflow.log_text(news_context, "context_news.txt")
                
                mlflow.log_metric("latency_seconds", time.time() - start_time)
        except Exception as e:
            logger.warning(f"MLflow Logging Failed: {e}")

        # Returns exact dictionary structure expected by your UI/App
        return {
            "symbol": symbol,
            "signal": canonical_signal,
            "prediction_token": final_pred,
            "prediction": final_pred,
            "confidence": confidence,
            "confidence_score": parsed.confidence,
            "reasoning": reasoning,
            "history_used": "symbolized_technical_context",
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

        response_text = await self._run_llm_text(prompt, temperature=0.7)
        return {"response": response_text or "I processed your request but could not generate a text response."}