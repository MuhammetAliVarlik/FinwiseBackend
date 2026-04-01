import mlflow
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta
import logging

from app.ml.symbolizer import FinwiseSymbolizer
from app.evaluation.thesis_metrics import ThesisMetrics
from app.core.config import settings
from app.core.label_contract import (
    UNKNOWN_LABEL,
    normalize_direction_label,
    normalize_prediction_token,
)

logger = logging.getLogger("scribe.evaluation")

class EvaluationService:
    """
    The 'Teacher' of the system.
    1. Fetches past predictions from MLflow.
    2. Fetches REAL market data to see what actually happened.
    3. Grades LLM vs LSTM.
    4. Logs 'Thesis Metrics' (McNemar/Alpha) back to MLflow.
    """

    def __init__(self):
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        self.metrics_engine = ThesisMetrics(experiment_name="Finwise_Thesis_Evaluation")

    def _get_actual_outcome(self, symbol: str, date_str: str) -> str:
        """
        Uses Symbolizer to verify what ACTUALLY happened on a specific date.
        """
        # We fetch a small window around the target date
        try:
            symbolizer = FinwiseSymbolizer(tickers=[symbol], period="1y")
            df = symbolizer.fetch_data()
            processed_df, _, tokens = symbolizer.process(df)

            if tokens.empty:
                return "UNKNOWN"

            if date_str:
                try:
                    target_date = pd.to_datetime(date_str, utc=True).tz_localize(None).date()
                    indexed = processed_df.copy()
                    indexed.index = pd.to_datetime(indexed.index)
                    same_day = indexed[indexed.index.date == target_date]
                    if not same_day.empty:
                        return str(same_day["Token"].iloc[-1])
                except Exception:
                    pass

            return str(tokens.iloc[-1])
        except Exception:
            return "UNKNOWN"

    def run_daily_evaluation(self):
        """
        Main Routine:
        1. Find all 'Prediction' runs from the last 24h.
        2. Check if they were right.
        3. Log the Significance Score.
        """
        logger.info("🚀 Starting Daily Thesis Evaluation...")
        
        # 1. Fetch Runs from the main experiment
        # We look for the experiment where engine.py logs predictions
        try:
            exp = mlflow.get_experiment_by_name("Finwise_RealTime_NeuroSymbolic")
            if not exp:
                logger.warning("No prediction experiment found yet.")
                return
            
            # Query runs from yesterday/today
            # (In prod, you'd filter by date, here we take last 50 for demo)
            runs = mlflow.search_runs(
                experiment_ids=[exp.experiment_id],
                max_results=50,
                order_by=["start_time DESC"]
            )
        except Exception as e:
            logger.error(f"Failed to fetch MLflow runs: {e}")
            return

        batch_results = []

        # 2. Grade Each Prediction
        for _, run in runs.iterrows():
            # Extract Logged Parameters with proper NaN handling
            # Note: MLflow return params with 'params.' prefix; missing params may be NaN (truthy)
            # Must explicitly check pd.notna() before using or to avoid NaN short-circuiting
            symbol = run.get("params.symbol")
            
            # Fallback logic: prefer slm_label, fall back to slm_prediction if missing/empty
            slm_label_val = run.get("params.slm_label")
            slm_pred_val = run.get("params.slm_prediction")
            llm_pred = None
            if pd.notna(slm_label_val) and str(slm_label_val).strip():
                llm_pred = slm_label_val
            elif pd.notna(slm_pred_val) and str(slm_pred_val).strip():
                llm_pred = slm_pred_val
            
            # Same for LSTM: prefer lstm_label, fall back to lstm_token
            lstm_label_val = run.get("params.lstm_label")
            lstm_token_val = run.get("params.lstm_token")
            lstm_pred = None
            if pd.notna(lstm_label_val) and str(lstm_label_val).strip():
                lstm_pred = lstm_label_val
            elif pd.notna(lstm_token_val) and str(lstm_token_val).strip():
                lstm_pred = lstm_token_val
            
            if not symbol or not llm_pred or not lstm_pred:
                continue

            # 3. Get Ground Truth (The "Reality Check")
            run_ts = run.get("start_time")
            run_date = None
            if run_ts is not None:
                run_date = pd.to_datetime(run_ts).strftime("%Y-%m-%d")

            actual_token = self._get_actual_outcome(symbol, run_date)

            llm_label = normalize_direction_label(llm_pred)
            if llm_label == UNKNOWN_LABEL:
                llm_label = normalize_prediction_token(llm_pred)

            lstm_label = normalize_direction_label(lstm_pred)
            if lstm_label == UNKNOWN_LABEL:
                lstm_label = normalize_prediction_token(lstm_pred)

            actual_label = normalize_prediction_token(actual_token)

            if UNKNOWN_LABEL in {llm_label, lstm_label, actual_label}:
                logger.warning(
                    "Skipping run due to unknown label normalization: symbol=%s llm=%s lstm=%s actual=%s",
                    symbol,
                    llm_pred,
                    lstm_pred,
                    actual_token,
                )
                continue
            
            # 4. Record Result
            batch_results.append({
                "llm": llm_label,
                "lstm": lstm_label,
                "actual": actual_label,
                "symbol": symbol
            })

        if not batch_results:
            logger.warning("No valid runs found to evaluate.")
            return

        # 5. Compute Thesis Metrics (McNemar / Alpha)
        self.metrics_engine.ingest_batch(batch_results)
        
        # 6. Log the 'Scorecard' to MLflow
        run_name = f"Daily_Evaluation_{datetime.now().strftime('%Y-%m-%d')}"
        self.metrics_engine.run_evaluation(run_name=run_name)
        
        logger.info(f"✅ Evaluation Complete. Processed {len(batch_results)} predictions.")
        return {
            "processed": len(batch_results),
            "status": "Logged to MLflow"
        }