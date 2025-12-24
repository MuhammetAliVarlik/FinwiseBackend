import React, { useRef, useEffect, useState } from 'react';
import { Send, Bot, BrainCircuit, Sparkles, FileText, X } from 'lucide-react';
import { ChatMessage, PredictionToken } from '../types';

interface AgentPanelProps {
  messages: ChatMessage[];
  currentInput: string;
  isTyping: boolean;
  onInputChange: (val: string) => void;
  onSend: () => void;
  contextSymbol: string;
}

// Simple Semi-Circle Gauge using SVG
const SentimentGauge = ({ signal, narrative }: { signal: number, narrative: number }) => {
    // 0 = Left (-90deg), 100 = Right (90deg)
    // Map 0-100 to -90 to 90
    const signalDeg = (signal / 100) * 180 - 90;
    const narrativeDeg = (narrative / 100) * 180 - 90;
    
    // Radius 40, Center 50,50
    return (
        <div className="flex flex-col items-center">
            <div className="relative w-32 h-16 overflow-hidden">
                <svg viewBox="0 0 100 50" className="w-full h-full">
                    {/* Background Arc */}
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

                    {/* Pivot */}
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

  return (
    <div className="h-full flex flex-col bg-zinc-900/50 border-l border-zinc-800 w-[30%] min-w-[350px] relative">
      
      {/* Header & Gauge */}
      <div className="border-b border-zinc-800 bg-zinc-900 p-4">
         <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-brand-purple" />
                <span className="text-sm font-semibold text-zinc-200">Llama-3 Reasoning</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-brand-purple/10 border border-brand-purple/20">
                <div className="w-1.5 h-1.5 rounded-full bg-brand-purple animate-pulse" />
                <span className="text-[10px] font-mono text-brand-purple">MEMORY ACTIVE</span>
            </div>
         </div>
         
         {/* Divergence Gauge */}
         <div className="bg-zinc-950 rounded-lg p-2 border border-zinc-800/50 shadow-inner">
             <SentimentGauge signal={30} narrative={85} />
         </div>
      </div>

      {/* Chat Stream */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth">
        {messages.map((msg) => (
            <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                
                {/* Avatar / Role Label */}
                <div className="mb-1 flex items-center gap-2">
                    {msg.role === 'agent' && <Bot className="w-3 h-3 text-brand-purple" />}
                    <span className="text-[10px] font-mono text-zinc-500 uppercase">
                        {msg.role === 'user' ? 'You' : 'Scribe Agent'}
                    </span>
                </div>

                {/* Bubble */}
                <div className={`
                    max-w-[90%] rounded-lg p-3 text-sm leading-relaxed
                    ${msg.role === 'user' 
                        ? 'bg-zinc-800 text-zinc-200 rounded-tr-none' 
                        : 'bg-zinc-950 border border-zinc-800 text-zinc-300 rounded-tl-none shadow-lg'
                    }
                `}>
                    {msg.content}
                </div>

                {/* Reasoning Widget / Mini Cards */}
                {msg.metadata?.forecastSummary && (
                    <div className="mt-3 w-[90%] bg-zinc-900 border border-zinc-800 rounded p-3 relative overflow-hidden group">
                        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-brand-blue to-brand-purple" />
                        <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-mono text-zinc-400">FORECAST SUMMARY</span>
                            <Sparkles className="w-3 h-3 text-brand-purple" />
                        </div>
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-lg font-bold text-white">{msg.metadata.forecastSummary.symbol}</h3>
                            <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                                msg.metadata.forecastSummary.prediction_token.includes('SURGE') 
                                ? 'bg-emerald-500/10 text-emerald-500' 
                                : 'bg-rose-500/10 text-rose-500'
                            }`}>
                                {msg.metadata.forecastSummary.prediction_token}
                            </span>
                        </div>
                        <div className="flex justify-between text-xs text-zinc-500 font-mono">
                            <span>Conf: {(msg.metadata.forecastSummary.confidence * 100).toFixed(0)}%</span>
                            <span>{msg.metadata.forecastSummary.history_used}</span>
                        </div>
                    </div>
                )}
            </div>
        ))}
        
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
                            // Mock export action
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
