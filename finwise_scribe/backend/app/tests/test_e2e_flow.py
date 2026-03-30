import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_full_neuro_symbolic_pipeline(client: AsyncClient):
    """
    In-process E2E-like flow:
    1. Trigger async forecast endpoint.
    2. Simulate completed worker result through AsyncResult.
    3. Validate final aggregated response contract.
    """
    with patch("app.controllers.forecast_controller.task_predict_shadow_mode") as mock_task, patch(
        "app.controllers.forecast_controller.AsyncResult"
    ) as mock_async_result:
        # Trigger phase
        mock_task_instance = MagicMock()
        mock_task_instance.id = "pipeline-task-001"
        mock_task.delay.return_value = mock_task_instance

        trigger_response = await client.post("/ai/forecast/BTC-USD")
        assert trigger_response.status_code == 202
        trigger_data = trigger_response.json()
        assert trigger_data["task_id"] == "pipeline-task-001"

        # Poll phase with completed result
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {
            "symbol": "BTC-USD",
            "prediction_token": "P_SURGE_V_HIGH",
            "signal": "BULLISH",
            "confidence": 0.85,
            "confidence_score": 85,
            "reasoning": "RSI_HIGH and TREND_BULLISH aligned with positive MACD.",
            "history_used": "symbolized_technical_context",
        }
        mock_async_result.return_value = mock_result

        poll_response = await client.get(f"/ai/tasks/{trigger_data['task_id']}")
        assert poll_response.status_code == 200
        poll_data = poll_response.json()

        assert poll_data["status"] == "completed"
        result = poll_data["result"]
        assert result["symbol"] == "BTC-USD"
        assert result["prediction_token"] == "P_SURGE_V_HIGH"
        assert result["signal"] == "BULLISH"
        assert result["confidence_score"] == 85