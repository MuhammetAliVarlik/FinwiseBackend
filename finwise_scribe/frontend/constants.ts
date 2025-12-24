import { ChartDataPoint, PredictionToken, Session, HeatmapCell, WatchlistItem, HistoricalMatch } from './types';

export const COLORS = {
  background: '#09090b',
  panel: '#18181b',
  input: '#27272a',
  border: '#27272a',
  text: '#e4e4e7',
  muted: '#a1a1aa',
  neonBlue: '#0ea5e9',
  profitGreen: '#10b981',
  lossRed: '#f43f5e',
  aiPurple: '#8b5cf6',
  slate: '#64748b'
};

export const MOCK_SESSIONS: Session[] = [
  { id: '1', title: 'MSFT: Q3 Earnings', date: '2h ago', isActive: true },
  { id: '2', title: 'BTC: Halving Event', date: '1d ago', isActive: false },
  { id: '3', title: 'NVDA: Volatility', date: '3d ago', isActive: false },
  { id: '4', title: 'Macro Trends 2024', date: '1w ago', isActive: false },
];

export const MOCK_WATCHLIST: WatchlistItem[] = [
  { symbol: 'AAPL', price: '182.40', change: '+1.2%', tokenState: 'P_SURGE' },
  { symbol: 'TSLA', price: '175.10', change: '-2.4%', tokenState: 'P_CRASH' },
  { symbol: 'BTC', price: '64,200', change: '+0.5%', tokenState: 'P_STEADY' },
  { symbol: 'AMD', price: '160.50', change: '+3.1%', tokenState: 'P_SURGE' },
  { symbol: 'SOL', price: '145.20', change: '-5.2%', tokenState: 'P_CRASH' },
];

export const MOCK_PATTERNS: HistoricalMatch[] = [
  { date: 'Nov 12, 2021', similarity: 0.94, regime: 'Late Cycle Blowoff' },
  { date: 'Mar 04, 2018', similarity: 0.88, regime: 'Correction Entry' },
];

export const GENERATE_HEATMAP_DATA = (): HeatmapCell[] => {
  const data: HeatmapCell[] = [];
  const currentX = 3;
  const currentY = 1;

  for (let x = 0; x < 5; x++) {
    for (let y = 0; y < 5; y++) {
      data.push({
        x,
        y,
        value: Math.random(),
        isCurrentState: x === currentX && y === currentY,
        label: `Q${x}${y}`
      });
    }
  }
  return data;
};

// Generate realistic looking market data
// Lightweight Charts prefers YYYY-MM-DD string for time
export const GENERATE_CHART_DATA = (days: number): ChartDataPoint[] => {
  const data: ChartDataPoint[] = [];
  let price = 150;
  
  // Create a base trend using sine wave + noise
  const now = new Date();
  
  for (let i = 0; i < days; i++) {
    // Calculate date string YYYY-MM-DD
    const date = new Date(now.getTime() - (days - 1 - i) * 24 * 60 * 60 * 1000);
    const dateStr = date.toISOString().split('T')[0];
    
    // Random Walk / Trend Math
    const trend = Math.sin(i / 15) * 5; 
    const noise = (Math.random() - 0.5) * 4;
    const volatility = Math.random() * 3 + 1;
    
    const change = trend * 0.1 + noise; 
    
    const open = price;
    const close = price + change;
    const high = Math.max(open, close) + Math.random() * volatility;
    const low = Math.min(open, close) - Math.random() * volatility;
    
    price = close;

    let token: PredictionToken | undefined = undefined;

    // Inject symbols on specific "events" logic
    // We'll simulate a token if price moves drastically or randomly sparsely
    const movePercent = Math.abs((close - open) / open);
    
    if (movePercent > 0.03) {
       // Big move
       if (close > open) token = PredictionToken.P_SURGE_V_HIGH;
       else token = PredictionToken.P_CRASH_V_HIGH;
    } else if (i % 25 === 0) {
       // Periodic analysis token
       token = PredictionToken.P_STABLE;
    }

    data.push({
      time: dateStr,
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      volume: Math.floor(Math.random() * 10000000) + 1000000,
      token
    });
  }
  return data;
};
