import { ChartDataPoint, ChatMessage, ForecastResponse, PredictionToken } from '../types';

// Access the environment variable (Vite style)
// Fallback to localhost:8000 if not set
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const ApiService = {
  
  // GET /forecast/{symbol}
  // Connects to Backend -> Scribe Service -> Ollama
  getForecast: async (symbol: string): Promise<ForecastResponse> => {
    try {
      const response = await fetch(`${API_URL}/forecast/${symbol}`);
      if (!response.ok) throw new Error('Forecast API failed');
      
      const data = await response.json();
      return {
        symbol: data.symbol,
        prediction_token: data.prediction as PredictionToken || PredictionToken.P_STABLE,
        history_used: data.history_used || 'Real-time Market Data',
        confidence: 0.85 // Placeholder as Llama output is text-based
      };
    } catch (e) {
      console.error("Forecast Error:", e);
      // Fallback for demo stability if model is loading
      return {
        symbol: symbol,
        prediction_token: PredictionToken.P_STABLE,
        history_used: 'Error fetching forecast',
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

  // POST /chat/message
  // Simple simulation for now, can be expanded to full RAG later
  sendMessage: async (sessionId: string, message: string, context: string): Promise<ChatMessage> => {
    // Simulate "Thinking..."
    await new Promise(r => setTimeout(r, 600));

    // For the demo, we interpret the forecast locally if the user asks
    // In Phase 4, this will call a real /chat endpoint
    
    let content = `I am analyzing the live symbolic stream for ${context}. `;
    
    if (message.toLowerCase().includes('forecast') || message.toLowerCase().includes('predict')) {
       // We can trigger a real forecast call here
       try {
         const forecast = await ApiService.getForecast(context);
         content += `My Llama-3 Engine predicts a **${forecast.prediction_token}** state based on the last 60 days of activity.`;
       } catch (e) {
         content += "I am currently unable to access the inference engine.";
       }
    } else {
       content += "I am monitoring volatility patterns. Ask me for a 'forecast' or 'outlook'.";
    }

    return {
      id: crypto.randomUUID(),
      role: 'agent',
      content,
      timestamp: new Date().toISOString()
    };
  }
};