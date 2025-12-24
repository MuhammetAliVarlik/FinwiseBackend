import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import MarketCanvas from './components/MarketCanvas';
import AgentPanel from './components/AgentPanel';
import { ApiService } from './services/api';
import { 
  MOCK_SESSIONS, 
  GENERATE_HEATMAP_DATA,
  GENERATE_CHART_DATA 
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

  return (
    <div className="flex h-screen w-screen bg-zinc-950 text-zinc-100 font-sans overflow-hidden selection:bg-brand-blue/30">
      
      {/* 1. Left Sidebar */}
      <Sidebar 
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSessionSelect={handleSessionSelect}
      />

      {/* 2. Center Canvas */}
      <MarketCanvas 
        symbol={currentSymbol}
        onSymbolChange={handleSymbolChange}
        chartData={chartData}
        heatmapData={heatmapData}
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
        isLoading={isChartLoading}
        regime={regime}
      />

      {/* 3. Right Agent Panel */}
      <AgentPanel 
        messages={chatMessages}
        currentInput={chatInput}
        onInputChange={setChatInput}
        onSend={handleSendMessage}
        isTyping={isAgentTyping}
        contextSymbol={currentSymbol}
      />

    </div>
  );
}

export default App;
