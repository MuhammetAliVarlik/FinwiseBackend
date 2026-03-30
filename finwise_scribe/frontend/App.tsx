import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import MarketCanvas from './components/MarketCanvas';
import AgentPanel from './components/AgentPanel';
import { ApiService } from './services/api';
import { 
  MOCK_SESSIONS, 
  GENERATE_HEATMAP_DATA,
} from './constants';
import { 
  ChartDataPoint, 
  ChatMessage, 
  Session, 
  HeatmapCell, 
  Timeframe,
  VolatilityRegime
} from './types';

function App() {
  // --- State ---
  const [sessions, setSessions] = useState<Session[]>(MOCK_SESSIONS);
  const [activeSessionId, setActiveSessionId] = useState<string>('1');
  
  const [currentSymbol, setCurrentSymbol] = useState<string>('MSFT');
  const [timeframe, setTimeframe] = useState<Timeframe>('1D');
  
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [heatmapData, setHeatmapData] = useState<HeatmapCell[]>([]);
  const [isChartLoading, setIsChartLoading] = useState<boolean>(true);

  // New Pro State
  const [regime, setRegime] = useState<VolatilityRegime>('P_STEADY');

  // Chat State
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState<string>('');
  const [isAgentTyping, setIsAgentTyping] = useState<boolean>(false);
  const [activeMobilePanel, setActiveMobilePanel] = useState<'sidebar' | 'market' | 'chat'>('market');
  const [activePage, setActivePage] = useState<'terminal' | 'sessions' | 'settings'>('terminal');

  // Desktop resizer state for center vs right panel
  const [agentPanelWidthPct, setAgentPanelWidthPct] = useState<number>(31);
  const [isResizing, setIsResizing] = useState<boolean>(false);
  const appRef = useRef<HTMLDivElement | null>(null);
  const [isDesktop, setIsDesktop] = useState<boolean>(() =>
    typeof window !== 'undefined' ? window.matchMedia('(min-width: 1024px)').matches : true
  );

  // Keyboard shortcut bridge for focusing the chat input from App level
  const [chatFocusPulse, setChatFocusPulse] = useState<number>(0);

  // --- Mock Data Helpers ---
  const getInitialMessagesForSession = (sessionId: string, symbol: string): ChatMessage[] => {
    const baseMessages: ChatMessage[] = [
      {
        id: `init-${sessionId}`,
        role: 'agent',
        content: `Session ${sessionId} initialized. Analyzing real-time symbolic data for ${symbol}. Market accumulation detected in Q3 quadrant.`,
        timestamp: new Date(Date.now() - 1000000).toISOString()
      }
    ];

    if (sessionId === '1') {
      baseMessages.push({
         id: 'msg-1-2',
         role: 'agent',
         content: 'I have detected unusual symbolic patterns on MSFT. The "P_SURGE_V_HIGH" token has appeared twice in the last session, indicating a potential breakout.',
         timestamp: new Date(Date.now() - 500000).toISOString()
      });
    }

    return baseMessages;
  };

  // --- Effects ---

  // Initialize Data
  useEffect(() => {
    // Initial Load
    setChatMessages(getInitialMessagesForSession('1', 'MSFT'));
    setHeatmapData(GENERATE_HEATMAP_DATA());
  }, []);

  // Load Market Data when Symbol or Timeframe changes
  useEffect(() => {
    const loadData = async () => {
      setIsChartLoading(true);
      try {
        const data = await ApiService.getMarketData(currentSymbol, timeframe);
        setChartData(data);
        // Refresh Heatmap randomly to simulate state change
        setHeatmapData(GENERATE_HEATMAP_DATA());
        
        // Randomly set regime based on symbol for demo purposes
        const regimes: VolatilityRegime[] = ['V_PEAK', 'P_STEADY', 'V_PEAK', 'P_STEADY'];
        const randomRegime = regimes[Math.floor(Math.random() * regimes.length)];
        setRegime(randomRegime);

      } catch (e) {
        console.error("Failed to load market data", e);
      } finally {
        setIsChartLoading(false);
      }
    };
    loadData();
  }, [currentSymbol, timeframe]);

  // Handle Session Switching Logic
  useEffect(() => {
    // When session changes, reload chat context
    const session = sessions.find(s => s.id === activeSessionId);
    if (session) {
      // Simulate fetching chat history
      setChatMessages(getInitialMessagesForSession(activeSessionId, currentSymbol));
    }
  }, [activeSessionId]);

  // Global keyboard shortcuts (roadmap-aligned power user UX)
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + P: Run forecast instantly
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'p') {
        e.preventDefault();
        handleRunForecast();
      }

      // Ctrl/Cmd + / : focus chat composer
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        setActiveMobilePanel('chat');
        setChatFocusPulse((v) => v + 1);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [currentSymbol]);

  useEffect(() => {
    if (!isResizing) return;

    const onMouseMove = (e: MouseEvent) => {
      if (!appRef.current) return;
      const rect = appRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const nextAgentPct = ((rect.width - x) / rect.width) * 100;
      const bounded = Math.max(24, Math.min(42, nextAgentPct));
      setAgentPanelWidthPct(bounded);
    };

    const onMouseUp = () => setIsResizing(false);

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [isResizing]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mql = window.matchMedia('(min-width: 1024px)');
    const handleChange = (e: MediaQueryListEvent) => setIsDesktop(e.matches);

    setIsDesktop(mql.matches);
    mql.addEventListener('change', handleChange);
    return () => mql.removeEventListener('change', handleChange);
  }, []);

  // --- Handlers ---

  const handleSessionSelect = (id: string) => {
    setActiveSessionId(id);
    setSessions(prev => prev.map(s => ({ ...s, isActive: s.id === id })));
  };

  const handleSymbolChange = (sym: string) => {
    setCurrentSymbol(sym.toUpperCase());
    // Inject a system message about context switch
    setChatMessages(prev => [
      ...prev, 
      {
        id: crypto.randomUUID(),
        role: 'agent',
        content: `Switched context to ${sym.toUpperCase()}. Loading historical volatility tokens...`,
        timestamp: new Date().toISOString()
      }
    ]);
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: chatInput,
      timestamp: new Date().toISOString()
    };

    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setIsAgentTyping(true);

    try {
      // Call Mocked API
      const agentResponse = await ApiService.sendMessage(activeSessionId, userMsg.content, currentSymbol);
      setChatMessages(prev => [...prev, agentResponse]);
    } catch (e) {
      console.error("Chat failed", e);
    } finally {
      setIsAgentTyping(false);
    }
  };

  // --- NEW: Handle Run Forecast ---
  const handleRunForecast = async () => {
    // 1. Show a loading message in chat
    const loadingMsgId = crypto.randomUUID();
    setChatMessages(prev => [...prev, {
      id: loadingMsgId,
      role: 'agent',
      content: `Initiating Shadow Mode analysis for ${currentSymbol}... Comparing Llama-3 vs LSTM baseline.`,
      timestamp: new Date().toISOString()
    }]);

    try {
      // 2. Call API
      const result = await ApiService.getForecast(currentSymbol);
      
      // 3. Remove loading msg and show Result Card
      setChatMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: crypto.randomUUID(),
          role: 'agent',
          content: "Analysis Complete. Here is the symbolic projection:",
          timestamp: new Date().toISOString(),
          // This metadata triggers the "Card" view in AgentPanel.tsx
          metadata: {
             forecastSummary: {
               symbol: result.symbol,
               prediction_token: result.prediction_token,
               confidence: result.confidence,
               history_used: result.history_used
             }
          }
        }];
      });

    } catch (e) {
      console.error(e);
      // Show error in chat
      setChatMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'agent',
        content: "Error: Could not retrieve forecast from Scribe Engine.",
        timestamp: new Date().toISOString()
      }]);
    }
  };

  return (
    <div
      ref={appRef}
      className="relative flex h-screen w-screen overflow-hidden bg-[#05070f] text-zinc-100 font-sans selection:bg-cyan-400/30"
    >
      <div className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(55%_75%_at_8%_0%,rgba(34,211,238,0.11),transparent_60%),radial-gradient(35%_40%_at_92%_8%,rgba(245,158,11,0.08),transparent_55%),linear-gradient(180deg,#05070f,#0a0f1b)]" />

      {/* Desktop Sidebar */}
      <div className="hidden lg:block h-full min-w-[260px] w-[18%] relative z-10">
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSessionSelect={handleSessionSelect}
          activePage={activePage}
          onPageChange={setActivePage}
        />
      </div>

      {/* Main area with responsive panel routing */}
      <div className="relative z-10 flex flex-1 h-full min-w-0">
        {!isDesktop && activeMobilePanel === 'sidebar' && (
          <div className="flex w-full h-full">
            <Sidebar
              sessions={sessions}
              activeSessionId={activeSessionId}
              onSessionSelect={handleSessionSelect}
              activePage={activePage}
              onPageChange={setActivePage}
            />
          </div>
        )}

        {activePage !== 'terminal' && !(activeMobilePanel === 'sidebar' && !isDesktop) && (
          <div className="flex-1 min-w-0 p-4 lg:p-8 overflow-y-auto">
            <div className="mx-auto max-w-5xl rounded-xl border border-cyan-900/25 bg-[#09101d]/80 backdrop-blur p-5 lg:p-8">
              {activePage === 'sessions' ? (
                <>
                  <h2 className="text-xl font-bold tracking-tight text-cyan-100">Sessions Archive</h2>
                  <p className="mt-2 text-sm text-zinc-300">Review previous analysis sessions and switch active context from the sidebar.</p>
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3">
                    {sessions.map((s) => (
                      <button
                        key={s.id}
                        onClick={() => {
                          handleSessionSelect(s.id);
                          setActivePage('terminal');
                          setActiveMobilePanel('chat');
                        }}
                        className="rounded-lg border border-zinc-700/70 bg-zinc-900/40 p-4 text-left hover:border-cyan-500/50 hover:bg-zinc-900/60 transition-colors"
                      >
                        <div className="text-sm font-semibold text-zinc-100">{s.title}</div>
                        <div className="text-xs text-zinc-400 mt-1">{s.date}</div>
                      </button>
                    ))}
                  </div>
                </>
              ) : (
                <>
                  <h2 className="text-xl font-bold tracking-tight text-amber-100">Workspace Settings</h2>
                  <p className="mt-2 text-sm text-zinc-300">Configure panel behavior and shortcuts. More controls can be added as needed.</p>
                  <div className="mt-6 space-y-3 text-sm text-zinc-200">
                    <div className="rounded-lg border border-zinc-700/70 bg-zinc-900/40 p-4">Shortcut: <span className="font-mono text-cyan-300">Ctrl/Cmd + P</span> runs forecast</div>
                    <div className="rounded-lg border border-zinc-700/70 bg-zinc-900/40 p-4">Shortcut: <span className="font-mono text-cyan-300">Ctrl/Cmd + /</span> focuses chat input</div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {activePage === 'terminal' && !(activeMobilePanel === 'sidebar' && !isDesktop) && (
          <>
            <div
              className={`min-w-0 ${activeMobilePanel === 'market' ? 'flex' : 'hidden'} lg:flex`}
              style={{ width: isDesktop ? `calc(100% - ${agentPanelWidthPct}%)` : '100%' }}
            >
              <MarketCanvas
                symbol={currentSymbol}
                onSymbolChange={handleSymbolChange}
                chartData={chartData}
                heatmapData={heatmapData}
                timeframe={timeframe}
                onTimeframeChange={setTimeframe}
                isLoading={isChartLoading}
                regime={regime}
                onForecast={handleRunForecast}
              />
            </div>

            {/* Desktop drag handle */}
            <button
              className="hidden lg:flex h-full w-2 items-center justify-center bg-transparent hover:bg-cyan-500/10 active:bg-cyan-500/20"
              onMouseDown={() => setIsResizing(true)}
              aria-label="Resize agent panel"
            >
              <span className="h-14 w-[2px] rounded-full bg-zinc-700" />
            </button>

            <div
              className={`min-w-0 ${activeMobilePanel === 'chat' ? 'flex' : 'hidden'} lg:flex`}
              style={{ width: isDesktop ? `min(100%, ${agentPanelWidthPct}%)` : '100%' }}
            >
              <AgentPanel
                messages={chatMessages}
                currentInput={chatInput}
                onInputChange={setChatInput}
                onSend={handleSendMessage}
                isTyping={isAgentTyping}
                contextSymbol={currentSymbol}
                focusPulse={chatFocusPulse}
              />
            </div>
          </>
        )}
      </div>

      {/* Mobile bottom nav */}
      <div className="lg:hidden absolute bottom-0 left-0 right-0 z-40 border-t border-cyan-900/40 bg-[#070c16]/95 backdrop-blur px-3 py-2">
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => setActiveMobilePanel('sidebar')}
            className={`rounded-md py-2 text-xs font-semibold tracking-wide ${
              activeMobilePanel === 'sidebar'
                ? 'bg-zinc-700/40 text-zinc-100 border border-zinc-500/50'
                : 'bg-zinc-900/60 text-zinc-400 border border-zinc-800'
            }`}
          >
            MENU
          </button>
          <button
            onClick={() => setActiveMobilePanel('market')}
            className={`rounded-md py-2 text-xs font-semibold tracking-wide ${
              activeMobilePanel === 'market'
                ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-500/40'
                : 'bg-zinc-900/60 text-zinc-400 border border-zinc-800'
            }`}
          >
            MARKET
          </button>
          <button
            onClick={() => setActiveMobilePanel('chat')}
            className={`rounded-md py-2 text-xs font-semibold tracking-wide ${
              activeMobilePanel === 'chat'
                ? 'bg-amber-400/20 text-amber-100 border border-amber-300/40'
                : 'bg-zinc-900/60 text-zinc-400 border border-zinc-800'
            }`}
          >
            SCRIBE
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;