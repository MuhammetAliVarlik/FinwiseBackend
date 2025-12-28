import httpx
import mlflow
import time
import os
import json
import re
import pandas as pd
from app.core.config import settings
from app.ml.symbolizer import FinwiseSymbolizer
from app.ml.lstm_engine import LSTMEngine

import httpx
import mlflow
import time
import os
import json
import re
import pandas as pd
from app.core.config import settings
from app.ml.symbolizer import FinwiseSymbolizer
from app.ml.lstm_engine import LSTMEngine

class ScribeEngine:
    def __init__(self):
        self.lstm = LSTMEngine()
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        mlflow.set_tracking_uri(mlflow_uri)
        try:
            mlflow.set_experiment("Finwise_Scribe_Shadow_Mode")
        except:
            pass

    async def _run_llm(self, prompt: str):
        """Helper to call Ollama and handle basic errors."""
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
                            "temperature": 0.1, # Keep low for JSON syntax
                            "stop": ["\n", "User:", "```"]
                        }
                    },
                    timeout=300.0
                )
                if response.status_code == 200:
                    return response.json().get("response", "{}")
            except Exception as e:
                print(f"LLM Error: {e}")
        return "{}"

    async def predict(self, symbol: str):
        start_time = time.time()
        
        # 1. Fetch Data
        try:
            symbolizer = FinwiseSymbolizer(tickers=[symbol], period="1y")
            raw_df = symbolizer.fetch_data()
            if raw_df.empty: return {"error": "No Data"}
            _, _, full_tokens = symbolizer.process(raw_df)
        except Exception as e:
            return {"error": f"Data Error: {e}"}

        # ==========================================
        # PHASE A: ROLLING VALIDATION
        # ==========================================
        VALIDATION_WINDOW = 3
        lstm_hits = 0
        llm_hits = 0
        validation_logs = []

        for i in range(1, VALIDATION_WINDOW + 1):
            target_idx = -i
            target_token = full_tokens.iloc[target_idx]
            cutoff_df = raw_df.iloc[:target_idx]
            
            # LSTM Backtest
            lstm_val = self.lstm.predict(symbol, data_override=cutoff_df)
            lstm_pred = lstm_val.get("prediction_token", "N/A")
            
            if lstm_pred == target_token:
                lstm_hits += 1
                
            # LLM Backtest
            start_idx = target_idx - 60
            if target_idx == -1:
                hist_tokens = full_tokens.iloc[start_idx:-1]
            else:
                hist_tokens = full_tokens.iloc[start_idx:target_idx]
                
            history_str = " ".join(hist_tokens.values)
            
            # IMPROVED PROMPT: Removes ambiguity
            val_prompt = (
                f"You are validating a financial model.\n"
                f"Token Vocabulary: P_[ACTION]_V_[VOLATILITY]\n"
                f"Sequence: [{history_str}]\n"
                f"Task: Predict the NEXT composite token.\n"
                f"Output: Valid JSON only. Do not use placeholders.\n"
                f"Example: {{ \"prediction\": \"P_SURGE_V_HIGH\" }}" 
            )
            
            llm_resp = await self._run_llm(val_prompt)
            
            # ROBUST PARSING
            try:
                # Strip markdown if present
                clean_resp = llm_resp.replace("```json", "").replace("```", "").strip()
                llm_json = json.loads(clean_resp)
                llm_pred = llm_json.get("prediction", "N/A").upper()
                
                # Check if model lazily copied the example
                if llm_pred == "P_SURGE_V_HIGH":
                    # Fallback check: Did the model really think it was surge?
                    # If not, try to extract first token from string
                    pass 
            except:
                llm_pred = "ERROR"
            
            if llm_pred == target_token:
                llm_hits += 1
            
            validation_logs.append({
                "day_offset": i,
                "target": target_token,
                "lstm_pred": lstm_pred,
                "llm_pred": llm_pred,
                "match_lstm": (lstm_pred == target_token),
                "match_llm": (llm_pred == target_token)
            })

        acc_lstm = lstm_hits / VALIDATION_WINDOW
        acc_llm = llm_hits / VALIDATION_WINDOW

        # ==========================================
        # PHASE B: FORECAST (Future)
        # ==========================================
        lstm_future = self.lstm.predict(symbol, data_override=raw_df)
        future_history = " ".join(full_tokens.tail(60).values)
        
        future_prompt = (
            f"You are Finwise Scribe. Analyze the last 60 days for {symbol}.\n"
            f"Token Vocabulary: P_[ACTION]_V_[VOLATILITY]\n"
            f"Data: [{future_history}]\n\n"
            f"Task: Predict the single most likely NEXT composite token.\n"
            f"Output Requirement: JSON Only. Calculate specific confidence.\n"
            f"Example: {{ \"prediction\": \"P_MID_V_LOW\", \"confidence\": 72, \"reasoning\": \"Trend is flattening...\" }}"
        )
        
        llm_future_resp = await self._run_llm(future_prompt)
        parsed_result = {"prediction": "P_STABLE_V_MID", "confidence": 50, "reasoning": "Processing..."}
        try:
            clean_future = llm_future_resp.replace("```json", "").replace("```", "").strip()
            parsed_result = json.loads(clean_future)
        except:
            pass

        # Normalize Confidence
        raw_conf = parsed_result.get("confidence", 50)
        final_conf = raw_conf / 100.0 if raw_conf > 1.0 else raw_conf

        # ==========================================
        # PHASE C: LOGGING
        # ==========================================
        try:
            with mlflow.start_run():
                mlflow.log_param("symbol", symbol)
                mlflow.log_metric("val_accuracy_lstm", acc_lstm)
                mlflow.log_metric("val_accuracy_llm", acc_llm)
                
                mlflow.log_param("forecast_lstm", lstm_future.get("prediction_token"))
                mlflow.log_param("forecast_llm", parsed_result.get("prediction"))
                mlflow.log_metric("llm_confidence", final_conf)
                
                mlflow.log_dict(validation_logs, "validation_details.json")
                mlflow.log_text(json.dumps(parsed_result), "output.json")
                mlflow.log_metric("inference_latency", time.time() - start_time)
        except Exception as e:
            print(f"MLflow Log Error: {e}")

        return {
            "symbol": symbol,
            "prediction": parsed_result.get("prediction", "P_STABLE_V_MID"),
            "confidence": final_conf,
            "reasoning": parsed_result.get("reasoning", ""),
            "shadow_baseline": lstm_future,
            "history_used": f"60 Days (+ {VALIDATION_WINDOW} Day Validation)"
        }

    async def chat(self, message: str, symbol: str):
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

        prompt = (
            f"### SYSTEM ROLE\n"
            f"You are Scribe, a Technical Analysis AI. You ONLY analyze price action patterns.\n"
            f"Token Structure: P_[ACTION]_V_[VOLATILITY]\n"
            f"### MARKET DATA (Last 30 Days)\n"
            f"Sequence: {context_str}\n\n"
            f"### USER QUESTION\n"
            f"{message}\n\n"
            f"### RESPONSE\n"
            f"(Answer based ONLY on the token sequence above. Be concise.)"
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": "finwise_scribe_v1", 
                        "prompt": prompt, 
                        "stream": False,
                        "options": {"temperature": 0.7}
                    },
                    timeout=300.0
                )
                if response.status_code != 200:
                    return {"response": "I'm having trouble thinking right now."}
                result = response.json()
                return {"response": result.get("response", "")}
            except Exception as e:
                return {"error": f"Chat inference failed: {str(e)}"}