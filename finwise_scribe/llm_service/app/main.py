from fastapi import FastAPI, HTTPException, BackgroundTasks
import logging
from app.schemas.prompt import EnginePredictionPayload
from pydantic import BaseModel
from typing import Any, Optional
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="Scribe LLM Engine", version="1.0.0")
engine = None
evaluator = None


def get_engine():
    global engine
    if engine is None:
        from app.services.engine import ScribeEngine

        engine = ScribeEngine()
    return engine


def get_evaluator():
    global evaluator
    if evaluator is None:
        from app.services.evaluation_service import EvaluationService

        evaluator = EvaluationService()
    return evaluator

class PredictionRequest(BaseModel):
    symbol: str
    market_data: Optional[dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    symbol: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/predict", response_model=EnginePredictionPayload)
async def predict_next_move(request: PredictionRequest):
    result = await get_engine().predict(request.symbol, request.market_data)
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
    background_tasks.add_task(get_evaluator().run_daily_evaluation)
    return {"message": "Thesis Evaluation started in background. Check MLflow shortly."}

@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    return await get_engine().chat(request.message, request.symbol)