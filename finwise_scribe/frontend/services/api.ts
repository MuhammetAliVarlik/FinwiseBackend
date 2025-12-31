import { ChartDataPoint, ChatMessage, ForecastResponse, PredictionToken, TaskResponse } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper: Pause execution for X milliseconds
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const ApiService = {
  
  // NEW: Polling Logic
  // Keeps checking the server until the job is done or times out
  pollTask: async (taskId: string, maxAttempts = 30): Promise<any> => {
    for (let i = 0; i < maxAttempts; i++) {
        try {
            const response = await fetch(`${API_URL}/ai/tasks/${taskId}`);
            if (!response.ok) throw new Error('Polling failed');
            
            const data: TaskResponse = await response.json();
            
            // 1. Success
            if (data.status === 'completed' || data.status === 'success') {
                // Check if the RESULT itself contains an error (from our new backend logic)
                if (data.result && data.result.error) {
                    throw new Error(data.result.error);
                }
                return data.result;
            }
            
            // 2. Failure (Celery failed)
            if (data.status === 'failed') {
                throw new Error(typeof data.result === 'string' ? data.result : 'Task failed on server');
            }
            
            // 3. Still Running
            await delay(2000);
            
        } catch (e: any) {
            // If the backend sent a specific error (like "Warming up"), re-throw it immediately
            if (e.message.includes("warming up") || e.message.includes("Unreachable")) {
                throw e;
            }
            console.warn(`Polling attempt ${i + 1} failed:`, e);
            await delay(2000);
        }
    }
    // Specific Timeout Message
    throw new Error('Server is busy (Model Loading). Please try again in a moment.');
  },
  

  // REFACTORED: Async Forecast
  getForecast: async (symbol: string): Promise<ForecastResponse> => {
    try {
      // 1. Trigger the background job (Fire & Forget)
      const triggerResponse = await fetch(`${API_URL}/ai/forecast/${symbol}`, {
          method: 'POST' // Changed from GET to POST
      });
      
      if (!triggerResponse.ok) throw new Error('Failed to start forecast task');
      
      const triggerData: TaskResponse = await triggerResponse.json();
      
      // 2. Poll until we get the result
      const result = await ApiService.pollTask(triggerData.task_id);
      
      // 3. Return the clean data
      return {
        symbol: result.symbol,
        prediction_token: result.prediction_token as PredictionToken,
        confidence: result.confidence,
        history_used: result.history_used
      };

    } catch (e) {
      console.error("Forecast Error:", e);
      // Graceful fallback for UI
      return {
        symbol: symbol,
        prediction_token: PredictionToken.P_STABLE,
        history_used: 'Error: Timeout or Service Down',
        confidence: 0.0
      };
    }
  },

  // GET /stocks/{symbol}/history
  getMarketData: async (symbol: string, timeframe: string): Promise<ChartDataPoint[]> => {
    try {
      const days = timeframe === '1W' ? 365 : timeframe === '1Y' ? 1000 : 100;
      
      const response = await fetch(`${API_URL}/stocks/${symbol}/history?timeframe=${timeframe}`);
      if (!response.ok) throw new Error('Market Data API failed');

      const rawData = await response.json();

      return rawData.map((d: any) => ({
        time: d.time,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
        token: undefined 
      }));
    } catch (e) {
      console.error("Market Data Error:", e);
      return [];
    }
  },

  // POST /ai/chat
  sendMessage: async (sessionId: string, message: string, context: string): Promise<ChatMessage> => {
    try {
      const response = await fetch(`${API_URL}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          symbol: context 
        })
      });

      if (!response.ok) throw new Error('Chat API failed');
      const data = await response.json();

      return {
        id: crypto.randomUUID(),
        role: 'agent',
        content: data.response || "I couldn't generate a response.",
        timestamp: new Date().toISOString()
      };

    } catch (e) {
      console.error("Chat Error:", e);
      return {
        id: crypto.randomUUID(),
        role: 'agent',
        content: "Error: I cannot reach the Scribe Engine right now.",
        timestamp: new Date().toISOString()
      };
    }
  }
};