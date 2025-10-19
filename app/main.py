# app/main.py
from fastapi import FastAPI
from controllers.user_controller import UserController
from controllers.stock_controller import StockController

app = FastAPI(title="FinwiseBackend Enterprise API")

# Routerları ekle
app.include_router(UserController().router)
app.include_router(StockController().router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Finwise Backend running."}
