from fastapi import FastAPI, HTTPException, BackgroundTasks
from app.services.engine import ScribeEngine
from app.services.evaluation_service import EvaluationService # <-- Import New Service
from app.schemas.prompt import EnginePredictionPayload
from pydantic import BaseModel
from typing import Any, Optional

app = FastAPI(title="Scribe LLM Engine", version="1.0.0")
engine = ScribeEngine()
evaluator = EvaluationService() # <-- Initialize

class PredictionRequest(BaseModel):
    symbol: str
    market_data: Optional[dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    symbol: str

@app.post("/predict", response_model=EnginePredictionPayload)
async def predict_next_move(request: PredictionRequest):
    result = await engine.predict(request.symbol, request.market_data)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# --- NEW ENDPOINT FOR THESIS EVALUATION ---
@app.post("/evaluate")
async def trigger_evaluation(background_tasks: BackgroundTasks):
    """
    Triggers the 'Ground Truth' analysis.
    Checks past MLflow predictions against current market data
    and logs the McNemar's Test results.
    """
    # Run in background so UI doesn't freeze
    background_tasks.add_task(evaluator.run_daily_evaluation)
    return {"message": "Thesis Evaluation started in background. Check MLflow shortly."}

@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    return await engine.chat(request.message, request.symbol)