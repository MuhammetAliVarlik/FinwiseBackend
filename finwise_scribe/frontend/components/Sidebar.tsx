import React, { useState } from 'react';
import { History, Zap, Activity, Settings, Terminal, List, BarChart2 } from 'lucide-react';
import { Session, WatchlistItem } from '../types';
import { MOCK_WATCHLIST } from '../constants';

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string;
  onSessionSelect: (id: string) => void;
    activePage?: 'terminal' | 'sessions' | 'settings';
    onPageChange?: (page: 'terminal' | 'sessions' | 'settings') => void;
}

const Sidebar: React.FC<SidebarProps> = ({ sessions, activeSessionId, onSessionSelect, activePage = 'terminal', onPageChange }) => {
  const [activeTab, setActiveTab] = useState<'sessions' | 'watchlist'>('watchlist');

  return (
    <aside className="h-full bg-[#070e19]/95 border-r border-cyan-900/25 flex flex-col justify-between w-full min-w-[240px]">
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
                <div className="p-5 flex items-center gap-3 border-b border-cyan-900/20 shrink-0">
                    <Terminal className="w-6 h-6 text-cyan-300" />
                    <h1 className="font-mono font-bold tracking-tight text-lg text-zinc-100">
                        FINWISE<span className="text-amber-300">_SCRIBE</span>
          </h1>
        </div>

        {/* Tab Switcher */}
        <div className="px-4 pt-4 shrink-0">
                        <div className="mb-3 rounded-md border border-zinc-800 bg-zinc-950/60 p-1 grid grid-cols-3 gap-1">
                                <button
                                    onClick={() => onPageChange?.('terminal')}
                                    className={`py-1.5 rounded text-[11px] font-semibold transition-colors ${activePage === 'terminal' ? 'bg-cyan-500/20 text-cyan-100 border border-cyan-500/30' : 'text-zinc-400 hover:text-zinc-200'}`}
                                >
                                    TERM
                                </button>
                                <button
                                    onClick={() => onPageChange?.('sessions')}
                                    className={`py-1.5 rounded text-[11px] font-semibold transition-colors ${activePage === 'sessions' ? 'bg-amber-400/20 text-amber-100 border border-amber-400/30' : 'text-zinc-400 hover:text-zinc-200'}`}
                                >
                                    SESS
                                </button>
                                <button
                                    onClick={() => onPageChange?.('settings')}
                                    className={`py-1.5 rounded text-[11px] font-semibold transition-colors ${activePage === 'settings' ? 'bg-zinc-700/60 text-zinc-100 border border-zinc-500/40' : 'text-zinc-400 hover:text-zinc-200'}`}
                                >
                                    CFG
                                </button>
                        </div>

            <div className="flex bg-zinc-900 p-1 rounded-md border border-zinc-800">
                <button 
                    onClick={() => setActiveTab('watchlist')}
                    className={`flex-1 flex items-center justify-center gap-2 py-1.5 text-xs font-medium rounded transition-all
                    ${activeTab === 'watchlist' ? 'bg-cyan-500/20 text-cyan-100 shadow-sm border border-cyan-500/30' : 'text-zinc-500 hover:text-zinc-300'}`}
                >
                    <Activity className="w-3 h-3" />
                    WATCH
                </button>
                <button 
                    onClick={() => setActiveTab('sessions')}
                    className={`flex-1 flex items-center justify-center gap-2 py-1.5 text-xs font-medium rounded transition-all
                    ${activeTab === 'sessions' ? 'bg-amber-400/15 text-amber-100 shadow-sm border border-amber-400/25' : 'text-zinc-500 hover:text-zinc-300'}`}
                >
                    <List className="w-3 h-3" />
                    MEM
                </button>
            </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto px-2 py-4 space-y-1">
            
            {activeTab === 'watchlist' && (
                <div className="space-y-1">
                    <h3 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-3 px-4">Live Symbols</h3>
                    {MOCK_WATCHLIST.map((item) => {
                        const isSurge = item.tokenState === 'P_SURGE';
                        const isCrash = item.tokenState === 'P_CRASH';
                        const dotColor = isSurge ? 'bg-emerald-500' : isCrash ? 'bg-rose-500' : 'bg-zinc-500';
                        const shadow = isSurge ? 'shadow-[0_0_8px_#10b981]' : isCrash ? 'shadow-[0_0_8px_#f43f5e]' : '';
                        
                        return (
                            <div key={item.symbol} className="group flex items-center justify-between px-3 py-3 rounded-md hover:bg-zinc-900/50 cursor-pointer border border-transparent hover:border-zinc-800 transition-all">
                                <div className="flex items-center gap-3">
                                    <div className="relative">
                                        <div className={`w-2 h-2 rounded-full ${dotColor} ${shadow} ${item.tokenState !== 'P_STEADY' ? 'animate-pulse' : ''}`} />
                                    </div>
                                    <div>
                                        <div className="text-sm font-bold text-zinc-200 group-hover:text-brand-blue font-mono">{item.symbol}</div>
                                        <div className="text-[10px] text-zinc-500 font-mono">{item.tokenState}</div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs font-mono text-white">{item.price}</div>
                                    <div className={`text-[10px] font-mono ${item.change.startsWith('+') ? 'text-emerald-500' : 'text-rose-500'}`}>
                                        {item.change}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {activeTab === 'sessions' && (
                 <div className="space-y-1">
                    <h3 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-3 px-4">Recent Sessions</h3>
                    {sessions.map((session) => (
                    <button
                        key={session.id}
                        onClick={() => onSessionSelect(session.id)}
                        className={`w-full text-left px-3 py-3 rounded-md text-sm font-medium transition-all group relative flex items-center gap-3
                        ${activeSessionId === session.id 
                            ? 'bg-zinc-900 text-brand-blue' 
                            : 'text-zinc-400 hover:bg-zinc-900/50 hover:text-zinc-200'
                        }`}
                    >
                        {activeSessionId === session.id && (
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 bg-brand-blue rounded-r-full shadow-[0_0_10px_#0ea5e9]" />
                        )}
                        <History className="w-4 h-4 opacity-70" />
                        <div className="flex flex-col overflow-hidden">
                             <span className="truncate">{session.title}</span>
                             <span className="text-[10px] text-zinc-600 font-mono">{session.date}</span>
                        </div>
                       
                    </button>
                    ))}
                </div>
            )}
        </div>
      </div>

      {/* Footer Status */}
    <div className="p-4 border-t border-cyan-900/20 bg-[#070e19] shrink-0">
        <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 bg-brand-green rounded-full shadow-[0_0_8px_#10b981]" />
            <span className="text-xs font-mono text-zinc-400">WS: CONNECTED (24ms)</span>
        </div>
        <div className="flex items-center justify-between text-zinc-500">
                        <button onClick={() => onPageChange?.('settings')} className={`transition-colors ${activePage === 'settings' ? 'text-zinc-100' : 'hover:text-white'}`} aria-label="Open settings page">
                            <Settings className="w-5 h-5" />
                        </button>
                        <button onClick={() => onPageChange?.('sessions')} className={`transition-colors ${activePage === 'sessions' ? 'text-zinc-100' : 'hover:text-white'}`} aria-label="Open sessions page">
                            <Activity className="w-5 h-5" />
                        </button>
                        <button onClick={() => onPageChange?.('terminal')} className={`transition-colors ${activePage === 'terminal' ? 'text-zinc-100' : 'hover:text-white'}`} aria-label="Open terminal page">
                            <Zap className="w-5 h-5" />
                        </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
