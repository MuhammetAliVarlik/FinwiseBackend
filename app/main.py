from fastapi import FastAPI
from app.controllers.user_controller import UserController
from app.controllers.stock_controller import StockController
from app.controllers.forecast_controller import ForecastController

app = FastAPI(title="FinwiseBackend Enterprise API")

user_controller = UserController()
stock_controller = StockController()
forecast_controller = ForecastController()

app.include_router(user_controller.router)
app.include_router(stock_controller.router)
app.include_router(forecast_controller.router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Finwise Backend running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)