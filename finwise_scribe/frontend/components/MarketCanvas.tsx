import React, { useState, useEffect } from 'react';
import { Search, Maximize2, GitBranch, AlertTriangle } from 'lucide-react';
import SymbolicChart from './SymbolicChart';
import HeatmapMatrix from './HeatmapMatrix';
import { ChartDataPoint, HeatmapCell, Timeframe, VolatilityRegime } from '../types';
import { MOCK_PATTERNS } from '../constants';

interface MarketCanvasProps {
  symbol: string;
  onSymbolChange: (sym: string) => void;
  chartData: ChartDataPoint[];
  heatmapData: HeatmapCell[];
  timeframe: Timeframe;
  onTimeframeChange: (tf: Timeframe) => void;
  isLoading: boolean;
  regime: VolatilityRegime;
}

const MarketCanvas: React.FC<MarketCanvasProps> = ({
  symbol,
  onSymbolChange,
  chartData,
  heatmapData,
  timeframe,
  onTimeframeChange,
  isLoading,
  regime
}) => {
  const [searchInput, setSearchInput] = useState(symbol);

  useEffect(() => {
    setSearchInput(symbol);
  }, [symbol]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
        onSymbolChange(searchInput.trim());
    }
  };

  // Determine background style based on Regime
  let bgGradient = 'bg-zinc-950';
  if (regime === 'V_PEAK') bgGradient = 'bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-rose-950/20 via-zinc-950 to-zinc-950';
  if (regime === 'P_STEADY') bgGradient = 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900/20 via-zinc-950 to-zinc-950';

  return (
    <main className={`flex-1 flex flex-col h-full relative overflow-hidden transition-colors duration-1000 ${bgGradient}`}>
      
      {/* Top Bar */}
      <div className="h-16 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-950/80 backdrop-blur-md z-10 sticky top-0">
        
        {/* Symbol Search */}
        <form onSubmit={handleSearchSubmit} className="relative group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-brand-blue transition-colors" />
          <input 
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-full pl-10 pr-4 py-1.5 text-sm font-mono text-white focus:outline-none focus:border-brand-blue w-48 transition-all focus:w-64 uppercase placeholder:normal-case"
            placeholder="Search Ticker..."
          />
        </form>

        {/* Regime Indicator Pills (Visual Only) */}
        <div className="flex items-center gap-4">
             {regime === 'V_PEAK' && (
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 animate-pulse">
                    <AlertTriangle className="w-3 h-3 text-rose-500" />
                    <span className="text-[10px] font-mono font-bold text-rose-500 tracking-wider">REGIME: V_PEAK</span>
                </div>
             )}
            
            {/* Timeframe Pills */}
            <div className="flex bg-zinc-900 rounded-md p-1 border border-zinc-800">
                {(['1D', '1W', '1Y'] as Timeframe[]).map((tf) => (
                    <button
                        key={tf}
                        onClick={() => onTimeframeChange(tf)}
                        className={`px-3 py-1 text-xs font-medium rounded transition-all ${
                            timeframe === tf 
                            ? 'bg-zinc-800 text-white shadow-sm border border-zinc-700' 
                            : 'text-zinc-500 hover:text-zinc-300'
                        }`}
                    >
                        {tf}
                    </button>
                ))}
            </div>
        </div>
      </div>

      {/* Main Visual: Chart */}
      <div className="flex-1 relative border-b border-zinc-800 p-4">
        {/* Subtle Grid Background Effect */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" 
            style={{ 
                backgroundImage: 'linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)', 
                backgroundSize: '40px 40px' 
            }} 
        />

        {/* Pattern Matcher HUD Overlay */}
        <div className="absolute top-4 right-4 z-20 w-64 bg-black/60 backdrop-blur-md border border-zinc-700/50 rounded-lg p-3 shadow-2xl overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-brand-purple to-transparent opacity-50" />
            <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono text-zinc-400 uppercase flex items-center gap-1">
                    <GitBranch className="w-3 h-3" />
                    Fractal Match
                </span>
                <span className="text-xs font-bold text-brand-purple">94%</span>
            </div>
            <div className="space-y-1">
                {MOCK_PATTERNS.map((p, idx) => (
                    <div key={idx} className="group flex items-center justify-between p-1.5 rounded hover:bg-white/5 cursor-crosshair transition-colors">
                        <div className="flex flex-col">
                            <span className="text-xs text-zinc-200 font-mono">{p.date}</span>
                            <span className="text-[9px] text-zinc-500 uppercase">{p.regime}</span>
                        </div>
                        <div className="w-1.5 h-1.5 rounded-full bg-zinc-600 group-hover:bg-brand-blue group-hover:shadow-[0_0_8px_#0ea5e9] transition-all" />
                    </div>
                ))}
            </div>
        </div>

        {/* Live Indicator */}
        <div className="absolute top-4 left-4 z-10 flex gap-2">
             <div className="bg-zinc-900/80 backdrop-blur border border-zinc-700 p-2 rounded flex items-center gap-2 shadow-sm">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-[10px] font-mono text-zinc-300">LIVE FEED</span>
            </div>
        </div>

        {isLoading ? (
            <div className="w-full h-full flex items-center justify-center">
                <div className="flex flex-col items-center gap-2">
                    <div className="w-8 h-8 border-2 border-brand-blue border-t-transparent rounded-full animate-spin" />
                    <span className="text-xs font-mono text-zinc-500 animate-pulse">FETCHING SERIES...</span>
                </div>
            </div>
        ) : (
             <SymbolicChart data={chartData} />
        )}
      </div>

      {/* Bottom Panel: Heatmap & Stats */}
      <div className="h-[240px] bg-zinc-950 p-6 flex gap-6 shrink-0 border-t border-zinc-800">
         {/* Stats Column */}
         <div className="w-1/3 min-w-[200px] flex flex-col justify-between p-4 bg-zinc-900/30 rounded-lg border border-zinc-800/50">
            <div>
                <h3 className="text-zinc-500 text-[10px] font-mono uppercase mb-2 tracking-widest">Technical Rating</h3>
                <div className="text-2xl font-bold text-white mb-1 tracking-tight">STRONG BUY</div>
                <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden mt-2">
                    <div className="h-full bg-brand-green w-[85%] shadow-[0_0_10px_#10b981]" />
                </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <div className="text-[10px] text-zinc-500 font-mono">VOLATILITY</div>
                    <div className={`text-sm font-mono font-bold ${regime === 'V_PEAK' ? 'text-rose-500' : 'text-emerald-500'}`}>
                        {regime === 'V_PEAK' ? 'CRITICAL (0.92)' : 'NORMAL (0.45)'}
                    </div>
                </div>
                <div>
                    <div className="text-[10px] text-zinc-500 font-mono">RSI (14)</div>
                    <div className="text-sm font-mono text-zinc-300">62.40</div>
                </div>
            </div>
         </div>

         {/* Heatmap Visual */}
         <div className="flex-1 min-w-[300px]">
            <HeatmapMatrix data={heatmapData} />
         </div>
      </div>

    </main>
  );
};

export default MarketCanvas;
