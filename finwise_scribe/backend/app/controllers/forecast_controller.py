from fastapi import HTTPException
from app.controllers.base_controller import BaseController
from app.services.inference_service import InferenceService

class ForecastController(BaseController):
    def __init__(self):
        super().__init__(prefix="/forecast", tags=["AI Forecasting"])
        self.inference_service = InferenceService()
        
        self.router.get("/{symbol}")(self.get_forecast)

    def get_forecast(self, symbol: str):
        try:
            result = self.inference_service.predict_next_move(symbol.upper())
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Sunucu hatası: {str(e)}")