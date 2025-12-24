from fastapi import FastAPI
from app.services.engine import ScribeEngine
from pydantic import BaseModel

app = FastAPI(title="Scribe LLM Engine", version="1.0.0")
engine = ScribeEngine()

class PredictionRequest(BaseModel):
    symbol: str

class ChatRequest(BaseModel):
    message: str
    symbol: str

@app.get("/")
def health():
    return {"status": "Scribe Engine Operational"}

@app.post("/predict")
async def predict_next_move(request: PredictionRequest):
    return await engine.predict(request.symbol)

@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    return await engine.chat(request.message, request.symbol)