import React from 'react';
import { Bot, Sparkles } from 'lucide-react';

interface LoadingIndicatorProps {
  modelName: string;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ modelName }) => {
  return (
    <div className="flex w-full gap-3 sm:gap-4 p-4 sm:p-5 bg-dark-900/40 border-y border-white/[0.03]">
      <div className="flex w-full max-w-3xl gap-3 sm:gap-4">
        <div className="flex-shrink-0 w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-dark-800 text-indigo-400 border border-white/10 flex items-center justify-center animate-pulse">
          <Bot className="w-4 h-4 sm:w-5 sm:h-5" />
        </div>

        <div className="flex flex-col items-start min-w-0">
          <div className="flex items-center gap-2 mb-1.5 text-xs text-indigo-400/90 font-medium px-1">
            <Sparkles className="w-3.5 h-3.5 animate-spin text-brand-500" />
            <span>Thinking locally with {modelName}...</span>
          </div>

          <div className="bg-dark-850/80 rounded-2xl rounded-tl-sm px-4 py-3 sm:px-5 sm:py-3.5 border border-white/[0.06] shadow-sm">
            <div className="flex items-center gap-1.5 py-1">
              <span className="w-2 h-2 rounded-full bg-indigo-500/80 animate-bounce [animation-delay:-0.3s]"></span>
              <span className="w-2 h-2 rounded-full bg-indigo-500/80 animate-bounce [animation-delay:-0.15s]"></span>
              <span className="w-2 h-2 rounded-full bg-indigo-500/80 animate-bounce"></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
