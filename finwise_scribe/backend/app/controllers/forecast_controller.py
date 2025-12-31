# app/controllers/forecast_controller.py
from fastapi import HTTPException
from celery.result import AsyncResult
from pydantic import BaseModel
from typing import Optional, Any

from app.controllers.base_controller import BaseController
from app.services.inference_service import InferenceService
from app.tasks import task_predict_shadow_mode

class ChatRequest(BaseModel):
    message: str
    symbol: str

# Schema for the Fire-and-Forget response
class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None

class ForecastController(BaseController):
    def __init__(self):
        super().__init__(prefix="/ai", tags=["AI Agent"])
        self.inference_service = InferenceService()
        
        # 1. Trigger the Job (Fire & Forget)
        self.router.add_api_route(
            "/forecast/{symbol}", 
            self.trigger_forecast, 
            methods=["POST"], 
            response_model=TaskResponse,
            status_code=202
        )

        # 2. Poll for Results (New Endpoint)
        self.router.add_api_route(
            "/tasks/{task_id}", 
            self.get_task_status, 
            methods=["GET"],
            response_model=TaskResponse
        )

        # Chat remains synchronous (for now)
        self.router.add_api_route(
            "/chat", 
            self.post_chat, 
            methods=["POST"]
        )

    async def trigger_forecast(self, symbol: str):
        """
        Starts the Shadow Mode inference in the background.
        Returns immediately with a Task ID.
        """
        try:
            # .delay() sends the message to Redis and returns immediately
            task = task_predict_shadow_mode.delay(symbol.upper())
            
            return {
                "task_id": task.id, 
                "status": "processing", 
                "result": None
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Queue Error: {str(e)}")

    async def get_task_status(self, task_id: str):
        """
        Checks Redis to see if the Worker is done.
        """
        try:
            task_result = AsyncResult(task_id)
            
            response = {
                "task_id": task_id,
                "status": task_result.status.lower(), # PENDING, STARTED, SUCCESS, FAILURE
                "result": None
            }

            if task_result.ready():
                if task_result.successful():
                    response["result"] = task_result.result
                    response["status"] = "completed"
                else:
                    response["status"] = "failed"
                    # Only return the string error, not the traceback, for security
                    response["result"] = str(task_result.result)
            
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Polling Error: {str(e)}")

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