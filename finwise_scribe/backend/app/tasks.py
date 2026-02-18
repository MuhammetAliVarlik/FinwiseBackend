import asyncio
from app.worker import celery_app
from app.services.inference_service import InferenceService
from app.core.database import AsyncSessionLocal
from app.repositories.stock_repository import StockRepository
from app.services.stock_service import StockService

# Helper to run async code in the synchronous Celery worker
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# The Async Logic (Data Fetching + AI Inference)
async def process_forecast(ticker: str):
    async with AsyncSessionLocal() as db:
        # 1. Initialize the Data Layer
        repo = StockRepository(db)
        stock_service = StockService(repo)
        inference_service = InferenceService()

        # 2. Get Real Math (RSI, MACD, etc.)
        # This calls the new method we just added to StockService
        technical_context = await stock_service.get_technical_analysis(ticker)
        
        # If no data exists (e.g., new stock), handle gracefully
        if not technical_context:
            return {"error": f"No historical data found for {ticker}"}

        # 3. Call the AI with the Math
        # We pass the technical_context into the NEW payload argument
        result = await inference_service.predict_next_move(
            ticker=ticker, 
            context_data=technical_context
        )
        
        # 4. Return combined result (so Frontend can see the math too)
        return {
            "symbol": ticker,
            "market_data": technical_context, # Sends RSI/MACD to frontend
            "ai_analysis": result
        }

@celery_app.task(bind=True, name="predict_shadow_mode")
def task_predict_shadow_mode(self, ticker: str):
    """
    Background task that Orchestrates the Forecast:
    1. Fetches DB Data
    2. Calculates Indicators
    3. Calls LLM
    """
    try:
        # Run the complex async logic
        return run_async(process_forecast(ticker))
        
    except Exception as e:
        # Retry logic for network blips
        raise self.retry(exc=e, countdown=5, max_retries=3)