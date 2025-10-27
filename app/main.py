# app/main.py
from fastapi import FastAPI
from app.core.database import Base, engine
from app.controllers.user_controller import UserController
from app.controllers.stock_controller import StockController

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinwiseBackend Enterprise API")

# Routerları ekle
app.include_router(UserController().router)
app.include_router(StockController().router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Finwise Backend running."}
