import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

# -------------------------------------------------------------------------
# TEST 1: Triggering the Forecast (Fire & Forget)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_trigger_forecast_success(client: AsyncClient):
    """
    Verifies that POST /forecast:
    1. Returns HTTP 202 (Accepted)
    2. Returns a Task ID
    3. Calls the Celery 'delay' method exactly once
    """
    # Patch the task object imported in the controller
    with patch("app.controllers.forecast_controller.task_predict_shadow_mode") as mock_task:
        # Setup the mock to return a fake Task object with an ID
        mock_task_instance = MagicMock()
        mock_task_instance.id = "mock-task-id-123"
        mock_task.delay.return_value = mock_task_instance

        # Make the request
        response = await client.post("/ai/forecast/AAPL")

        # Assertions
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "mock-task-id-123"
        assert data["status"] == "processing"
        
        # Verify that the backend actually tried to send it to Redis
        mock_task.delay.assert_called_once_with("AAPL")


# -------------------------------------------------------------------------
# TEST 2: Polling Status (Pending)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_poll_status_pending(client: AsyncClient):
    """
    Verifies that GET /tasks/{id} handles a running task correctly.
    """
    # Patch AsyncResult (the library that talks to Redis)
    with patch("app.controllers.forecast_controller.AsyncResult") as mock_async_result:
        # Mock the state of a PENDING task
        mock_result = MagicMock()
        mock_result.status = "PENDING"
        mock_result.ready.return_value = False
        mock_async_result.return_value = mock_result

        response = await client.get("/ai/tasks/mock-task-id-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["result"] is None


# -------------------------------------------------------------------------
# TEST 3: Polling Status (Completed)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_poll_status_completed(client: AsyncClient):
    """
    Verifies that GET /tasks/{id} returns the result when the task is done.
    """
    with patch("app.controllers.forecast_controller.AsyncResult") as mock_async_result:
        # Mock the state of a SUCCESSFUL task
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        
        # This is the fake "Shadow Mode" result
        mock_result.result = {
            "symbol": "AAPL",
            "lstm_prediction": 150.00,
            "llm_analysis": "BULLISH"
        }
        
        mock_async_result.return_value = mock_result

        response = await client.get("/ai/tasks/mock-task-id-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"]["llm_analysis"] == "BULLISH"