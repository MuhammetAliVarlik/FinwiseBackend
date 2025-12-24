from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.user_controller import UserController
from app.controllers.stock_controller import StockController
from app.controllers.forecast_controller import ForecastController
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Finwise Scribe Microservice API"
)

# --- CORS Middleware ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
user_controller = UserController()
stock_controller = StockController()
forecast_controller = ForecastController()

app.include_router(user_controller.router)
app.include_router(stock_controller.router)
app.include_router(forecast_controller.router)

@app.get("/")
def health_check():
    """CI/CD Health Check Endpoint"""
    return {
        "status": "ok",
        "env": settings.ENVIRONMENT,
        "service": "Finwise Backend"
    }