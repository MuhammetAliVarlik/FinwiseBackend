import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, CrosshairMode, IChartApi, ISeriesApi } from 'lightweight-charts';
import { ChartDataPoint, PredictionToken } from '../types';
import { COLORS } from '../constants';

interface SymbolicChartProps {
  data: ChartDataPoint[];
}

const SymbolicChart: React.FC<SymbolicChartProps> = ({ data }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 1. Initialize Chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: COLORS.background },
        textColor: COLORS.slate,
      },
      grid: {
        vertLines: { color: '#1f1f22' },
        horzLines: { color: '#1f1f22' },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      timeScale: {
        borderColor: '#27272a',
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: '#27272a',
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
    });

    chartRef.current = chart;

    // 2. Add Candlestick Series
    const candleSeries = chart.addCandlestickSeries({
      upColor: COLORS.profitGreen,
      downColor: COLORS.lossRed,
      borderVisible: false,
      wickUpColor: COLORS.profitGreen,
      wickDownColor: COLORS.lossRed,
    });

    // 3. Format Data for Lightweight Charts
    // Lightweight charts requires sorted data by time.
    // Our generate function produces sorted data.
    const lcData = data.map(d => ({
      time: d.time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    candleSeries.setData(lcData);

    // 4. Generate Markers from PredictionTokens
    const markers = data
      .filter(d => d.token) // Only points with tokens
      .map(d => {
        const isSurge = d.token && d.token.includes('SURGE');
        return {
          time: d.time,
          position: isSurge ? 'aboveBar' : 'belowBar',
          color: isSurge ? COLORS.profitGreen : COLORS.lossRed,
          shape: isSurge ? 'arrowUp' : 'arrowDown',
          text: d.token?.replace('P_', ''),
          size: 2, // Relative size
        };
      });
    
    // @ts-ignore - markers type definition mismatch in some TS versions for mocks
    candleSeries.setMarkers(markers);

    // 5. Add Volume Series (Histogram) for extra realism
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // Overlay on same scale or separate? separate is better usually but overlay is simpler for layout
    });
    
    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8, // Highest volume bar takes up bottom 20%
        bottom: 0,
      },
    });

    const volumeData = data.map(d => ({
      time: d.time,
      value: d.volume,
      color: d.close > d.open ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.2)',
    }));
    
    volumeSeries.setData(volumeData);


    // 6. Handle Resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ 
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight
        });
      }
    };

    window.addEventListener('resize', handleResize);
    
    // Initial fit
    chart.timeScale().fitContent();

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data]);

  return (
    <div className="w-full h-full relative group">
      <div ref={chartContainerRef} className="w-full h-full" />
      
      {/* Overlay Badge */}
      <div className="absolute top-4 left-4 z-10 pointer-events-none">
         <div className="bg-zinc-900/80 backdrop-blur border border-zinc-700 p-2 rounded flex flex-col gap-1">
            <span className="text-[10px] text-zinc-500 font-mono uppercase">Symbolic Engine</span>
            <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-brand-blue rounded-full animate-pulse shadow-[0_0_8px_#0ea5e9]"></span>
                <span className="text-xs font-mono text-white">ACTIVE</span>
            </div>
         </div>
      </div>
    </div>
  );
};

export default SymbolicChart;