import React from 'react';
import {
  Cpu,
  Trash2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { HealthResponse } from '../types/api';

interface HeaderProps {
  health: HealthResponse | null;
  isHealthChecking: boolean;
  models: string[];
  selectedModel: string;
  onSelectModel: (model: string) => void;
  onClearHistory: () => void;
  onRefreshHealth: () => void;
  isClearing: boolean;
  messageCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  isHealthChecking,
  models,
  selectedModel,
  onSelectModel,
  onClearHistory,
  onRefreshHealth,
  isClearing,
  messageCount,
}) => {
  const isOllamaConnected = health?.ollama_reachable ?? false;
  const isBackendConnected = health !== null;

  return (
    <header className="flex-shrink-0 flex items-center justify-between px-4 sm:px-6 py-3.5 bg-dark-900/90 border-b border-white/[0.06] backdrop-blur-md z-10 shadow-sm">
      {/* Brand & Title */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-indigo-400 flex items-center justify-center text-white shadow-lg shadow-brand-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-semibold text-base sm:text-lg tracking-tight text-white">
              Offline AI Assistant
            </h1>
            <span className="hidden sm:inline-block text-[11px] font-medium tracking-wide uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              100% Local
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            Private on-device LLM inference via Ollama
          </p>
        </div>
      </div>

      {/* Control Actions & Status */}
      <div className="flex items-center gap-2.5 sm:gap-4">
        {/* Model Selector Dropdown */}
        <div className="flex items-center gap-1.5 bg-dark-850 px-2.5 py-1.5 rounded-xl border border-white/[0.08] shadow-inner">
          <Cpu className="w-4 h-4 text-indigo-400 hidden xs:inline" />
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            disabled={models.length === 0}
            className="bg-transparent text-xs sm:text-sm font-medium text-slate-200 outline-none cursor-pointer pr-1 py-0.5 max-w-[140px] sm:max-w-[200px] truncate"
          >
            {models.length > 0 ? (
              models.map((m) => (
                <option key={m} value={m} className="bg-dark-900 text-slate-200">
                  {m}
                </option>
              ))
            ) : (
              <option value="" className="bg-dark-900 text-slate-400">
                {isBackendConnected ? 'No models found' : 'Connecting...'}
              </option>
            )}
          </select>
        </div>

        {/* Backend / Ollama Status Indicator */}
        <button
          onClick={onRefreshHealth}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-dark-850 border border-white/[0.08] text-xs font-medium hover:border-white/20 transition-colors"
          title="Click to re-check connection"
        >
          {isBackendConnected && isOllamaConnected ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-subtle"></span>
              <span className="text-emerald-400 hidden sm:inline">Ollama Active</span>
            </>
          ) : isBackendConnected && !isOllamaConnected ? (
            <>
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-amber-400 hidden sm:inline">Ollama Offline</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-rose-500"></span>
              <span className="text-rose-400 hidden sm:inline">Backend Offline</span>
            </>
          )}
          <RotateCcw
            className={`w-3 h-3 text-slate-400 ${isHealthChecking ? 'animate-spin' : ''}`}
          />
        </button>

        {/* Clear Conversation History Button */}
        {messageCount > 0 && (
          <button
            onClick={onClearHistory}
            disabled={isClearing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-dark-850 hover:bg-rose-950/40 text-slate-300 hover:text-rose-400 border border-white/[0.08] hover:border-rose-900/40 text-xs font-medium transition-all shadow-sm active:scale-95 disabled:opacity-50"
            title="Reset conversation history for this session"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-400/80" />
            <span className="hidden md:inline">Clear</span>
          </button>
        )}
      </div>
    </header>
  );
};
