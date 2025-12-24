import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama

MODEL_PATH = "/app/models/finwise_scribe_v1.gguf"
HOST = "0.0.0.0"
PORT = 8001 

app = FastAPI(title="Finwise AI Engine")

llm_model = None

class PredictionRequest(BaseModel):
    prompt: str
    max_tokens: int = 10

@app.on_event("startup")
def load_model():
    global llm_model
    print(f"AI Engine starting... Model: {MODEL_PATH}")
    
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model not found: {MODEL_PATH}")
        return

    try:
        llm_model = Llama(
            model_path=MODEL_PATH,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=-1, 
            verbose=False
        )
        print("Model uploaded to RAM and ready to use!")
    except Exception as e:
        print(f"Model uploading error: {e}")

@app.post("/generate")
def generate_text(req: PredictionRequest):
    if not llm_model:
        raise HTTPException(status_code=503, detail="Model has not loaded yet.")
    
    output = llm_model(
        req.prompt,
        max_tokens=req.max_tokens,
        stop=["\n", "Response:"],
        echo=False
    )
    return {"text": output['choices'][0]['text'].strip()}

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)