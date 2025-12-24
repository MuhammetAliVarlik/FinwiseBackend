import { ChartDataPoint, ChatMessage, ForecastResponse, PredictionToken } from '../types';
import { GENERATE_CHART_DATA } from '../constants';

// Simulated latency
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const ApiService = {
  
  // GET /forecast/{symbol}
  getForecast: async (symbol: string): Promise<ForecastResponse> => {
    await delay(800);
    return {
      symbol: symbol.toUpperCase(),
      prediction_token: Math.random() > 0.5 ? PredictionToken.P_SURGE_V_HIGH : PredictionToken.P_STABLE,
      history_used: '60 days of OHLCV data + Sentiment',
      confidence: 0.85 + (Math.random() * 0.1)
    };
  },

  // GET /market/data/{symbol}
  getMarketData: async (symbol: string, timeframe: string): Promise<ChartDataPoint[]> => {
    // Generate data locally
    await delay(400); // Small load time
    const days = timeframe === '1W' ? 60 : timeframe === '1Y' ? 365 : 100;
    return GENERATE_CHART_DATA(days);
  },

  // POST /chat/message
  // Fully simulated locally
  sendMessage: async (sessionId: string, message: string, context: string): Promise<ChatMessage> => {
    await delay(1200); // Simulate "Thinking..."

    const lowerMsg = message.toLowerCase();
    let content = '';
    let metadata: any = undefined;

    // Scenario A: Outlook Query
    if (lowerMsg.includes('outlook') || lowerMsg.includes('predict') || lowerMsg.includes('forecast')) {
        content = `Based on the latest symbolic aggregation, ${context} is showing strong bullish divergence. The P_SURGE_V_HIGH token presence suggests institutional accumulation.`;
        metadata = {
            forecastSummary: {
                symbol: context,
                prediction_token: PredictionToken.P_SURGE_V_HIGH,
                history_used: 'Last 60 Days',
                confidence: 0.89
            }
        };
    } 
    // Scenario B: Risk/Volatility
    else if (lowerMsg.includes('risk') || lowerMsg.includes('volatility')) {
        content = `Volatility levels are elevated but stable. The heatmap indicates we are transitioning from Quadrant 3 (Accumulation) to Quadrant 1 (Expansion). Risk is moderate.`;
    }
    // Default
    else {
        content = `I've analyzed the recent price action for ${context}. I detected a generic pattern consistent with previous quarterly cycles. Do you want to see the support levels?`;
    }

    return {
      id: crypto.randomUUID(),
      role: 'agent',
      content,
      timestamp: new Date().toISOString(),
      metadata
    };
  }
};