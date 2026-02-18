import mlflow
import numpy as np
from scipy.stats import chi2
from typing import List, Dict, Optional

class ThesisMetrics:
    """
    Calculates statistical significance for Neuro-Symbolic comparisons
    and logs the 'Thesis Artifacts' directly to MLflow.
    """

    # FIX: Add 'experiment_name' to the constructor
    def __init__(self, experiment_name: str = "Finwise_Thesis_Evaluation"):
        self.contingency = {"a": 0, "b": 0, "c": 0, "d": 0}
        self.experiment_name = experiment_name
        
        # Set up MLflow
        try:
            mlflow.set_experiment(experiment_name)
        except Exception:
            pass # Experiment might already exist or MLflow isn't reachable yet

    def ingest_batch(self, results: List[Dict]):
        """
        Ingests a list of comparison results.
        Format: { "llm": "P_SURGE", "lstm": "P_MID", "actual": "P_SURGE" }
        """
        for row in results:
            llm_correct = row['llm'] == row['actual']
            lstm_correct = row['lstm'] == row['actual']

            if llm_correct and lstm_correct:
                self.contingency["a"] += 1 # Both Correct
            elif lstm_correct and not llm_correct:
                self.contingency["b"] += 1 # LSTM Wins (Regression)
            elif llm_correct and not lstm_correct:
                self.contingency["c"] += 1 # LLM Wins (Alpha)
            else:
                self.contingency["d"] += 1 # Both Wrong

    def run_evaluation(self, run_name="Shadow_Mode_Significance_Test"):
        """
        Calculates stats and logs EVERYTHING to MLflow.
        """
        b = self.contingency["b"]
        c = self.contingency["c"]
        total = sum(self.contingency.values())

        # 1. McNemar's Test (Chi-Squared)
        if (b + c) > 0:
            chi_sq = (abs(b - c) - 1)**2 / (b + c)
            p_value = chi2.sf(chi_sq, 1)
        else:
            chi_sq = 0.0
            p_value = 1.0

        # 2. Divergence Alpha (Prob of LLM Win given Disagreement)
        divergence_count = b + c
        divergence_alpha = c / divergence_count if divergence_count > 0 else 0.0

        # 3. Log to MLflow
        # Check if we are already in a run (if called from engine.py context)
        # If not, start one.
        active_run = mlflow.active_run()
        if active_run:
             self._log_metrics(total, divergence_count, c, b, chi_sq, p_value, divergence_alpha)
        else:
            with mlflow.start_run(run_name=run_name):
                self._log_metrics(total, divergence_count, c, b, chi_sq, p_value, divergence_alpha)

    def _log_metrics(self, total, divergence_count, wins_llm, wins_lstm, chi_sq, p_value, divergence_alpha):
        """Helper to log metrics to current run"""
        # A. Log the Counts (The Evidence)
        mlflow.log_metric("count_total", total)
        mlflow.log_metric("count_agreement", self.contingency["a"] + self.contingency["d"])
        mlflow.log_metric("count_divergence", divergence_count)
        mlflow.log_metric("wins_llm", wins_llm)
        mlflow.log_metric("wins_lstm", wins_lstm)

        # B. Log the Thesis Metrics (The Proof)
        mlflow.log_metric("thesis_chi_squared", chi_sq)
        mlflow.log_metric("thesis_p_value", p_value)
        mlflow.log_metric("thesis_divergence_alpha", divergence_alpha)

        # C. Log Tags for Filtering
        mlflow.set_tag("statistically_significant", "YES" if p_value < 0.05 else "NO")
        mlflow.set_tag("model_type", "neuro_symbolic_hybrid")

        # D. Log the "Conclusion" as text artifact
        conclusion = (
            f"Evaluation Results:\n"
            f"-------------------\n"
            f"Total Samples: {total}\n"
            f"Models Disagreed: {divergence_count} times\n"
            f"LLM Superiority Score (Alpha): {round(divergence_alpha * 100, 2)}%\n"
            f"P-Value: {round(p_value, 5)} "
            f"({'Significant' if p_value < 0.05 else 'Not Significant'})\n"
        )
        mlflow.log_text(conclusion, "thesis_conclusion.txt")