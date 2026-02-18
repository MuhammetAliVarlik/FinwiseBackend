import React, { useRef, useEffect, useState } from 'react';
import { Send, Bot, BrainCircuit, Sparkles, FileText, X, TrendingUp, Activity } from 'lucide-react';
import { ChatMessage } from '../types';

interface AgentPanelProps {
  messages: ChatMessage[];
  currentInput: string;
  isTyping: boolean;
  onInputChange: (val: string) => void;
  onSend: () => void;
  contextSymbol: string;
}

// Simple Semi-Circle Gauge
const SentimentGauge = ({ signal, narrative }: { signal: number, narrative: number }) => {
    const signalDeg = (signal / 100) * 180 - 90;
    const narrativeDeg = (narrative / 100) * 180 - 90;
    
    return (
        <div className="flex flex-col items-center">
            <div className="relative w-32 h-16 overflow-hidden">
                <svg viewBox="0 0 100 50" className="w-full h-full">
                    <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#27272a" strokeWidth="6" strokeLinecap="round" />
                    {/* Signal Needle (Red) */}
                    <line 
                        x1="50" y1="50" x2="50" y2="15" 
                        stroke="#f43f5e" strokeWidth="2" strokeLinecap="round"
                        transform={`rotate(${signalDeg} 50 50)`}
                        className="transition-transform duration-700 ease-out opacity-80"
                    />
                    {/* Narrative Needle (Green) */}
                    <line 
                        x1="50" y1="50" x2="50" y2="15" 
                        stroke="#10b981" strokeWidth="2" strokeLinecap="round"
                        transform={`rotate(${narrativeDeg} 50 50)`}
                        className="transition-transform duration-1000 ease-out opacity-80"
                    />
                    <circle cx="50" cy="50" r="3" fill="#52525b" />
                </svg>
            </div>
            <div className="flex w-full justify-between px-2 text-[9px] font-mono text-zinc-500 uppercase mt-1">
                <span className="text-rose-500">Tech Signal</span>
                <span className="text-emerald-500">AI Narrative</span>
            </div>
        </div>
    );
};

const AgentPanel: React.FC<AgentPanelProps> = ({ 
  messages, 
  currentInput, 
  isTyping, 
  onInputChange, 
  onSend,
  contextSymbol
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showExportModal, setShowExportModal] = useState(false);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  // Helper to safely get the display string
  const getPredictionLabel = (summary: any) => {
      // Support new format OR old format
      const val = summary.prediction || summary.prediction_token || "NEUTRAL";
      return typeof val === 'string' ? val : "PROCESSING";
  };

  return (
    <div className="h-full flex flex-col bg-zinc-900/50 border-l border-zinc-800 w-[30%] min-w-[350px] relative">
      
      {/* Header & Gauge */}
      <div className="border-b border-zinc-800 bg-zinc-900 p-4">
         <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-brand-purple" />
                <span className="text-sm font-semibold text-zinc-200">Scribe Logic Engine</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-brand-purple/10 border border-brand-purple/20">
                <div className="w-1.5 h-1.5 rounded-full bg-brand-purple animate-pulse" />
                <span className="text-[10px] font-mono text-brand-purple">ONLINE</span>
            </div>
         </div>
         
         <div className="bg-zinc-950 rounded-lg p-2 border border-zinc-800/50 shadow-inner">
             <SentimentGauge signal={45} narrative={70} />
         </div>
      </div>

      {/* Chat Stream */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth">
        {messages.map((msg) => {
            // Pre-calculate label to prevent crashes inside JSX
            const predLabel = msg.metadata?.forecastSummary ? getPredictionLabel(msg.metadata.forecastSummary) : "";
            const isBullish = predLabel.toUpperCase().includes("BULL") || predLabel.includes("RISE") || predLabel.includes("SURGE");
            const isBearish = predLabel.toUpperCase().includes("BEAR") || predLabel.includes("DROP") || predLabel.includes("FALL");

            return (
            <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                
                {/* Avatar */}
                <div className="mb-1 flex items-center gap-2">
                    {msg.role === 'agent' && <Bot className="w-3 h-3 text-brand-purple" />}
                    <span className="text-[10px] font-mono text-zinc-500 uppercase">
                        {msg.role === 'user' ? 'You' : 'Scribe Agent'}
                    </span>
                </div>

                {/* Bubble */}
                {msg.content && (
                    <div className={`
                        max-w-[90%] rounded-lg p-3 text-sm leading-relaxed
                        ${msg.role === 'user' 
                            ? 'bg-zinc-800 text-zinc-200 rounded-tr-none' 
                            : 'bg-zinc-950 border border-zinc-800 text-zinc-300 rounded-tl-none shadow-lg'
                        }
                    `}>
                        {msg.content}
                    </div>
                )}

                {/* --- NEW: NEURO-SYMBOLIC WIDGET --- */}
                {msg.metadata?.forecastSummary && (
                    <div className="mt-3 w-[95%] bg-zinc-900 border border-zinc-800 rounded p-3 relative overflow-hidden group shadow-xl">
                        {/* Gradient Bar */}
                        <div className={`absolute top-0 left-0 w-1 h-full bg-gradient-to-b ${
                            isBullish ? "from-emerald-500 to-emerald-700" 
                            : isBearish ? "from-rose-500 to-rose-700"
                            : "from-zinc-500 to-zinc-700"
                        }`} />
                        
                        <div className="flex justify-between items-start mb-2 pl-2">
                            <span className="text-xs font-mono text-zinc-400">MARKET SIGNAL</span>
                            <Sparkles className="w-3 h-3 text-brand-purple" />
                        </div>

                        {/* Prediction Header */}
                        <div className="flex items-center justify-between mb-3 pl-2">
                            <h3 className="text-xl font-bold text-white tracking-tight">{msg.metadata.forecastSummary.symbol}</h3>
                            <span className={`text-xs font-bold font-mono px-2 py-1 rounded border ${
                                isBullish ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                                : isBearish ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                                : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                            }`}>
                                {predLabel}
                            </span>
                        </div>

                        {/* Logic & Reasoning Box */}
                        <div className="pl-2 mb-3">
                             <div className="text-[11px] text-zinc-400 bg-zinc-950/50 p-2 rounded border border-zinc-800 leading-relaxed italic">
                                "{msg.metadata.forecastSummary.reasoning || "Analyzing market structure..."}"
                             </div>
                        </div>

                        {/* Technical Data Tags (Safe Check) */}
                        {msg.metadata.forecastSummary.market_data && (
                             <div className="pl-2 flex gap-2 mb-2">
                                <div className="flex items-center gap-1 bg-zinc-800/50 px-1.5 py-0.5 rounded border border-zinc-700">
                                    <Activity className="w-3 h-3 text-brand-blue" />
                                    <span className="text-[10px] text-zinc-300 font-mono">
                                        RSI: {msg.metadata.forecastSummary.market_data.rsi || "N/A"}
                                    </span>
                                </div>
                                <div className="flex items-center gap-1 bg-zinc-800/50 px-1.5 py-0.5 rounded border border-zinc-700">
                                    <TrendingUp className="w-3 h-3 text-brand-purple" />
                                    <span className="text-[10px] text-zinc-300 font-mono">
                                        {msg.metadata.forecastSummary.market_data.trend || "Wait"}
                                    </span>
                                </div>
                             </div>
                        )}

                        <div className="flex justify-between text-[10px] text-zinc-500 font-mono pl-2 border-t border-zinc-800/50 pt-2 mt-2">
                            <span>Conf: {(msg.metadata.forecastSummary.confidence * 100).toFixed(0)}%</span>
                            <span>Src: {msg.metadata.forecastSummary.history_used || "Live Data"}</span>
                        </div>
                    </div>
                )}
            </div>
        )})}
        
        {isTyping && (
            <div className="flex items-start gap-2">
                 <Bot className="w-3 h-3 text-brand-purple mt-1" />
                 <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 rounded-tl-none">
                    <div className="flex gap-1">
                        <div className="w-1.5 h-1.5 bg-zinc-600 rounded-full animate-bounce" style={{ animationDelay: '0ms'}} />
                        <div className="w-1.5 h-1.5 bg-zinc-600 rounded-full animate-bounce" style={{ animationDelay: '150ms'}} />
                        <div className="w-1.5 h-1.5 bg-zinc-600 rounded-full animate-bounce" style={{ animationDelay: '300ms'}} />
                    </div>
                 </div>
            </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-zinc-900 border-t border-zinc-800 z-10">
        <div className="mb-2 flex items-center justify-between">
            <span className="text-[10px] text-zinc-500 font-mono flex items-center gap-1">
                Context: <span className="text-brand-blue">{contextSymbol}</span>
            </span>
            <button 
                onClick={() => setShowExportModal(true)}
                className="text-[10px] text-zinc-500 hover:text-white flex items-center gap-1 transition-colors"
            >
                <FileText className="w-3 h-3" />
                EXPORT BRIEF
            </button>
        </div>
        <div className="relative">
            <textarea
                value={currentInput}
                onChange={(e) => onInputChange(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask Scribe about patterns..."
                className="w-full bg-zinc-950 border border-zinc-700 rounded-lg pl-3 pr-10 py-3 text-sm focus:outline-none focus:border-brand-purple focus:ring-1 focus:ring-brand-purple/50 resize-none h-12"
            />
            <button 
                onClick={onSend}
                disabled={!currentInput.trim() || isTyping}
                className="absolute right-2 top-2 p-1.5 bg-zinc-800 hover:bg-brand-purple text-zinc-400 hover:text-white rounded-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <Send className="w-4 h-4" />
            </button>
        </div>
      </div>

      {/* Export Modal Overlay */}
      {showExportModal && (
        <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6">
            <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow-2xl w-full max-w-sm overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="flex items-center justify-between p-4 border-b border-zinc-800">
                    <h3 className="text-sm font-bold text-white font-mono">GENERATE BRIEF</h3>
                    <button onClick={() => setShowExportModal(false)} className="text-zinc-500 hover:text-white">
                        <X className="w-4 h-4" />
                    </button>
                </div>
                <div className="p-4 space-y-4">
                    <div className="space-y-1">
                        <label className="text-[10px] uppercase text-zinc-500 font-mono">Focus Symbol</label>
                        <div className="text-lg font-bold text-white">{contextSymbol}</div>
                    </div>
                    <div className="space-y-1">
                        <label className="text-[10px] uppercase text-zinc-500 font-mono">Included Datasets</label>
                        <div className="flex flex-wrap gap-2">
                            <span className="px-2 py-1 bg-zinc-800 rounded text-[10px] text-zinc-300 border border-zinc-700">Sentiment Analysis</span>
                            <span className="px-2 py-1 bg-zinc-800 rounded text-[10px] text-zinc-300 border border-zinc-700">Technical Patterns</span>
                            <span className="px-2 py-1 bg-zinc-800 rounded text-[10px] text-zinc-300 border border-zinc-700">Fractal History</span>
                        </div>
                    </div>
                    <button 
                        onClick={() => {
                            setTimeout(() => setShowExportModal(false), 500);
                        }}
                        className="w-full py-2 bg-brand-blue hover:bg-sky-500 text-white font-bold rounded text-xs transition-colors"
                    >
                        DOWNLOAD PDF (PREVIEW)
                    </button>
                </div>
            </div>
        </div>
      )}

    </div>
  );
};

export default AgentPanel;