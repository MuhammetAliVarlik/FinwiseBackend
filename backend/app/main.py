from fastapi import FastAPI
from app.controllers.user_controller import UserController
from app.controllers.stock_controller import StockController
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Finwise Scribe Microservice API"
)

# Register Routers
user_controller = UserController()
stock_controller = StockController()

app.include_router(user_controller.router)
app.include_router(stock_controller.router)

@app.get("/")
def health_check():
    """CI/CD Health Check Endpoint"""
    return {
        "status": "ok",
        "env": settings.ENVIRONMENT,
        "service": "Finwise Backend"
    }