import { ChartDataPoint, ChatMessage, ForecastResponse, PredictionToken } from '../types';

// Access the environment variable (Vite style)
// Fallback to localhost:8000 if not set
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const ApiService = {
  
  // GET /forecast/{symbol}
  // Connects to Backend -> Scribe Service -> Ollama
  getForecast: async (symbol: string): Promise<ForecastResponse> => {
    try {
      const response = await fetch(`${API_URL}/ai/forecast/${symbol}`);
      if (!response.ok) throw new Error('Forecast API failed');
      
      const data = await response.json();
      
      return {
        symbol: data.symbol,
        // Use the REAL values from backend
        prediction_token: data.prediction as PredictionToken, 
        confidence: data.confidence, // This is now real (e.g. 0.92)
        history_used: data.history_used
      };
    } catch (e) {
      console.error("Forecast Error:", e);
      return {
        symbol: symbol,
        prediction_token: PredictionToken.P_STABLE,
        history_used: 'Error',
        confidence: 0.0
      };
    }
  },

  // GET /stocks/{symbol}/history
  // Connects to Backend -> StockService -> Stooq
  getMarketData: async (symbol: string, timeframe: string): Promise<ChartDataPoint[]> => {
    try {
      // Map timeframe to days
      const days = timeframe === '1W' ? 365 : timeframe === '1Y' ? 1000 : 100;
      
      const response = await fetch(`${API_URL}/stocks/${symbol}/history?timeframe=${timeframe}`);
      if (!response.ok) throw new Error('Market Data API failed');

      const rawData = await response.json();

      // Transform backend format (lowercase) to ChartDataPoint
      return rawData.map((d: any) => ({
        time: d.time, // "2023-01-01"
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
        // Token logic could be added here or calculated on frontend
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
      // 1. Send user message to Backend
      const response = await fetch(`${API_URL}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          symbol: context // e.g., "AAPL"
        })
      });

      if (!response.ok) throw new Error('Chat API failed');
      const data = await response.json();

      // 2. Return the LLM's response
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