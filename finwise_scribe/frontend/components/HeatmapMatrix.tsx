import React from 'react';
import { HeatmapCell } from '../types';

interface HeatmapMatrixProps {
  data: HeatmapCell[];
}

const HeatmapMatrix: React.FC<HeatmapMatrixProps> = ({ data }) => {
  return (
    <div className="w-full h-full p-4 bg-zinc-900/30 border border-zinc-800 rounded-lg">
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-xs font-mono text-zinc-400 uppercase tracking-widest">Universal Symbolizer Quantiles</h4>
        <span className="text-[10px] text-zinc-500 font-mono">STATE: Q3-1 (ACCUMULATION)</span>
      </div>
      
      <div className="grid grid-cols-5 gap-1 h-32 w-full">
        {data.map((cell) => (
          <div
            key={`${cell.x}-${cell.y}`}
            className={`
              relative flex items-center justify-center rounded-sm transition-all duration-500
              ${cell.isCurrentState ? 'border border-brand-blue shadow-[0_0_10px_#0ea5e9]' : 'border border-transparent'}
            `}
            style={{
              backgroundColor: `rgba(14, 165, 233, ${cell.value * 0.3})`
            }}
          >
            <span className={`text-[10px] font-mono ${cell.isCurrentState ? 'text-white font-bold' : 'text-zinc-600'}`}>
                {cell.value.toFixed(2)}
            </span>
            
            {/* Active Blip */}
            {cell.isCurrentState && (
                <div className="absolute top-0.5 right-0.5 w-1 h-1 bg-white rounded-full animate-pulse" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default HeatmapMatrix;
