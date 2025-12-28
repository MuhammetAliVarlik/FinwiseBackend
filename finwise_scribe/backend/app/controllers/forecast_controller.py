# app/controllers/forecast_controller.py
from fastapi import HTTPException
from pydantic import BaseModel
from app.controllers.base_controller import BaseController
from app.services.inference_service import InferenceService

class ChatRequest(BaseModel):
    message: str
    symbol: str

class ForecastController(BaseController):
    def __init__(self):
        super().__init__(prefix="/ai", tags=["AI Agent"])
        # Service is stateless (HTTP client), so simple init is fine
        self.inference_service = InferenceService()
        
        # Standardized routing to match Stock/User controllers
        self.router.add_api_route(
            "/forecast/{symbol}", self.get_forecast, methods=["GET"]
        )
        self.router.add_api_route(
            "/chat", self.post_chat, methods=["POST"]
        )

    async def get_forecast(self, symbol: str):
        try:
            result = await self.inference_service.predict_next_move(symbol.upper())
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

    async def post_chat(self, request: ChatRequest):
        try:
            result = await self.inference_service.chat(request.message, request.symbol)
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Chat Error: {str(e)}")