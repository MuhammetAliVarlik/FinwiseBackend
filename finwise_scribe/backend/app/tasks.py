import asyncio
from app.worker import celery_app
from app.services.inference_service import InferenceService

# Helper to run async code in the synchronous Celery worker
def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@celery_app.task(bind=True, name="predict_shadow_mode")
def task_predict_shadow_mode(self, ticker: str):
    """
    Background task that calls the Neuro-Symbolic Engine.
    This runs in the 'worker' container, NOT the API container.
    """
    service = InferenceService()
    
    try:
        # We wrap the async call because Celery workers are sync by default
        result = run_async(service.predict_next_move(ticker))
        
        # Check if the service returned a logical error (like Scribe down)
        if isinstance(result, dict) and "error" in result:
             # You might want to log this or raise a specific exception
             pass

        return result
        
    except Exception as e:
        # Retry logic: If the Scribe engine is momentarily down, retry in 5s.
        # max_retries=3 prevents infinite loops.
        raise self.retry(exc=e, countdown=5, max_retries=3)