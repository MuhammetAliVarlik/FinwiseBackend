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
        self.inference_service = InferenceService()
        
        self.router.get("/forecast/{symbol}")(self.get_forecast)
        self.router.post("/chat")(self.post_chat)

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
                # This raises a 400 error
                raise HTTPException(status_code=400, detail=result["error"])
            return result
            
        # FIXED: Catch HTTPException separately so it propagates correctly
        except HTTPException as he:
            raise he
        except Exception as e:
            # Only catch unexpected crashes here
            raise HTTPException(status_code=500, detail=f"Chat Error: {str(e)}")