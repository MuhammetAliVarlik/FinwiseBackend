import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

from app.ml.symbolizer import FinwiseSymbolizer

class InferenceService:
    _model_instance = None  # Singleton Pattern

    def __init__(self):
        if os.environ.get("TESTING") == "true":
            self.model = None
            print("⚠️ Test environment detected, model not loaded.")
            return
        
        base_path = os.getcwd()
        self.model_path = os.path.join(base_path, "models", "finwise_scribe_v1.gguf")
        
        if InferenceService._model_instance is None:
            print(f"🧠 Searching for model: {self.model_path}...")
            if not os.path.exists(self.model_path):
                alt_path = "/app/models/finwise_scribe_v1.gguf"
                if os.path.exists(alt_path):
                    self.model_path = alt_path
                else:
                    print("⚠️ WARNING: Model file not found! Prediction service will not work.")
                    self.model = None
                    return

            try:
                print("🚀 Loading model into RAM...")
                if Llama is None:
                    print("❌ llama-cpp-python library not found.")
                    return

                InferenceService._model_instance = Llama(
                    model_path=self.model_path,
                    n_ctx=2048,
                    n_threads=4,
                    n_gpu_layers=-1,
                    verbose=False
                )
                print("✅ Model successfully loaded!")
            except Exception as e:
                print(f"❌ Error while loading model: {e}")
                pass
        
        self.model = InferenceService._model_instance

    def predict_next_move(self, symbol: str):
        if not self.model:
            return {"error": "Model is not loaded or not found."}

        try:
            symbolizer = FinwiseSymbolizer(tickers=[symbol], period="10y", n_quantiles=5)
            raw_df = symbolizer.fetch_data()
            
            if raw_df.empty:
                return {"error": f"No data found for {symbol}."}

            _, _, text_series = symbolizer.process(raw_df)
            
            if len(text_series) < 60:
                return {"error": "Not enough historical data (Minimum 60 days required)."}

            history_str = " ".join(text_series.iloc[-60:].values)
            
            prompt = (
                f"Predict the next market token for {symbol} based on history:\n"
                f"{history_str}\nResponse:"
            )

            output = self.model(
                prompt,
                max_tokens=10,
                stop=["\n", "Response:"],
                echo=False
            )
            
            prediction_text = output['choices'][0]['text'].strip()
            
            return {
                "symbol": symbol,
                "prediction_token": prediction_text,
                "history_used": "Last 60 Days",
                "model_version": "Finwise-Scribe-v1"
            }
            
        except Exception as e:
            return {"error": f"Error during prediction: {str(e)}"}
