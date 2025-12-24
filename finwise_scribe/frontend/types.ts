export interface Session {
  id: string;
  title: string;
  date: string;
  isActive: boolean;
}

export enum PredictionToken {
  P_SURGE_V_HIGH = 'P_SURGE_V_HIGH',
  P_SURGE_MED = 'P_SURGE_MED',
  P_CRASH_V_HIGH = 'P_CRASH_V_HIGH',
  P_CRASH_MED = 'P_CRASH_MED',
  P_STABLE = 'P_STABLE',
  P_VOL_SPIKE = 'P_VOL_SPIKE'
}

export interface ChartDataPoint {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  token?: PredictionToken; // The symbolic overlay
}

export interface ForecastResponse {
  symbol: string;
  prediction_token: PredictionToken;
  history_used: string;
  confidence: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: string;
  metadata?: {
    forecastSummary?: ForecastResponse;
    relatedTopics?: string[];
  };
}

export interface HeatmapCell {
  x: number;
  y: number;
  value: number; // 0-1 for opacity
  isCurrentState: boolean;
  label: string;
}

export type Timeframe = '1D' | '1W' | '1Y';

// --- New Pro Types ---

export interface WatchlistItem {
  symbol: string;
  price: string;
  change: string;
  tokenState: 'P_SURGE' | 'P_CRASH' | 'P_STEADY';
}

export type VolatilityRegime = 'V_PEAK' | 'V_ELEVATED' | 'P_STEADY' | 'P_ACCUMULATION';

export interface HistoricalMatch {
  date: string;
  similarity: number;
  regime: string;
}
