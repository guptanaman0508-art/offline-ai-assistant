import React, { useState, useEffect, useRef } from 'react';
import { api } from './services/api';
import { ChatMessage, HealthResponse } from './types/api';
import { Header } from './components/Header';
import { MessageItem } from './components/MessageItem';
import { ChatInput } from './components/ChatInput';
import { LoadingIndicator } from './components/LoadingIndicator';
import { EmptyState } from './components/EmptyState';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('llama3.2:3b');
  const [sessionId, setSessionId] = useState<string>(() => {
    // Generate or restore session ID from browser session storage
    const stored = sessionStorage.getItem('offline_ai_session_id');
    if (stored) return stored;
    const newId = `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    sessionStorage.setItem('offline_ai_session_id', newId);
    return newId;
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isHealthChecking, setIsHealthChecking] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest response
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Initial load: Fetch health and model catalog
  const checkHealthAndModels = async () => {
    setIsHealthChecking(true);
    setErrorMessage(null);
    try {
      const healthData = await api.getHealth();
      setHealth(healthData);

      if (healthData.ollama_reachable) {
        try {
          const modelsData = await api.getModels();
          setModels(modelsData.models);
          if (modelsData.models.length > 0 && !modelsData.models.includes(selectedModel)) {
            setSelectedModel(modelsData.models[0]);
          }
        } catch (err: any) {
          console.warn('Could not fetch models:', err);
        }
      }
    } catch (err: any) {
      setHealth(null);
      setErrorMessage(
        'Backend connection failed. Make sure the FastAPI server is running with `uvicorn src.api.main:app --port 8000`.'
      );
    } finally {
      setIsHealthChecking(false);
    }
  };

  useEffect(() => {
    checkHealthAndModels();
  }, []);

  // Send Chat message handler
  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isLoading) return;

    setErrorMessage(null);

    // 1. Append user message to UI state immediately
    const userMessage: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // 2. Call backend /chat endpoint
    try {
      const response = await api.sendChat({
        message: text,
        model: selectedModel,
        session_id: sessionId,
      });

      // Update sessionId if server resolved/assigned one
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
        sessionStorage.setItem('offline_ai_session_id', response.session_id);
      }

      const assistantMessage: ChatMessage = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        latencySeconds: response.latency_seconds,
        model: response.model,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errText = err.message || 'An error occurred while generating response.';
      const errorMessageItem: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${errText}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessageItem]);
      setErrorMessage(errText);
    } finally {
      setIsLoading(false);
    }
  };

  // Clear conversation history handler
  const handleClearHistory = async () => {
    if (isClearing) return;
    setIsClearing(true);
    try {
      await api.clearHistory(sessionId);
      setMessages([]);
      setErrorMessage(null);
    } catch (err: any) {
      console.error('Failed to clear history on backend:', err);
      // Clear UI locally anyway
      setMessages([]);
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-dark-950 text-slate-100 select-none sm:select-auto">
      {/* Top Header */}
      <Header
        health={health}
        isHealthChecking={isHealthChecking}
        models={models}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        onClearHistory={handleClearHistory}
        onRefreshHealth={checkHealthAndModels}
        isClearing={isClearing}
        messageCount={messages.length}
      />

      {/* Global Error Banner if backend/Ollama disconnects */}
      {errorMessage && !isLoading && (
        <div className="bg-rose-950/60 border-b border-rose-800/40 px-4 py-2.5 flex items-center justify-between text-xs sm:text-sm text-rose-200 animate-fade-in">
          <div className="flex items-center gap-2 max-w-3xl mx-auto w-full">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span className="truncate">{errorMessage}</span>
          </div>
          <button
            onClick={checkHealthAndModels}
            className="flex items-center gap-1 px-2 py-0.5 rounded bg-rose-900/40 hover:bg-rose-900/80 border border-rose-700/50 text-xs font-medium ml-2"
          >
            <RefreshCw className="w-3 h-3" /> Retry
          </button>
        </div>
      )}

      {/* Main Chat Scroll Container */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden flex flex-col scrollbar-thin">
        {messages.length === 0 ? (
          <EmptyState
            selectedModel={selectedModel}
            onSelectPrompt={(prompt) => handleSendMessage(prompt)}
          />
        ) : (
          <div className="flex flex-col py-2 sm:py-4">
            {messages.map((msg) => (
              <MessageItem key={msg.id} message={msg} />
            ))}
            {isLoading && <LoadingIndicator modelName={selectedModel} />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Input Composer */}
      <footer className="flex-shrink-0 bg-gradient-to-t from-dark-950 via-dark-950/90 to-transparent pt-3">
        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSend={() => handleSendMessage()}
          isLoading={isLoading}
          disabled={health === null}
        />
      </footer>
    </div>
  );
};

export default App;
