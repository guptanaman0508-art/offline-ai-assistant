import React, { useRef, useEffect } from 'react';
import { Send, CornerDownLeft } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSend,
  isLoading,
  disabled = false,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea according to contents
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter without Shift sends the prompt
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && !disabled && value.trim()) {
        onSend();
      }
    }
  };

  const isSendDisabled = disabled || isLoading || !value.trim();

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4 sm:pb-6">
      <div className="relative flex flex-col bg-dark-900/90 rounded-2xl border border-white/[0.08] focus-within:border-brand-500/60 focus-within:ring-2 focus-within:ring-brand-500/20 shadow-2xl backdrop-blur-md transition-all duration-200">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          placeholder={
            disabled
              ? 'Backend is disconnected. Please check server status...'
              : 'Ask a question, request note explanations, or generate exam questions... (Shift+Enter for newline)'
          }
          rows={1}
          className="w-full bg-transparent text-slate-100 placeholder:text-slate-500 text-sm sm:text-base px-4 py-3.5 pr-14 resize-none outline-none max-h-44 scrollbar-thin"
        />

        <div className="flex items-center justify-between px-3.5 pb-2.5 pt-1 text-xs text-slate-500">
          <div className="flex items-center gap-1.5 hidden sm:flex">
            <span className="flex items-center gap-0.5 text-[11px] px-1.5 py-0.5 rounded bg-white/[0.04] text-slate-400 border border-white/[0.06]">
              <CornerDownLeft className="w-2.5 h-2.5" /> Enter
            </span>
            <span>to send</span>
            <span>•</span>
            <span className="text-[11px] px-1.5 py-0.5 rounded bg-white/[0.04] text-slate-400 border border-white/[0.06]">
              Shift+Enter
            </span>
            <span>for new line</span>
          </div>

          <div className="ml-auto">
            <button
              onClick={onSend}
              disabled={isSendDisabled}
              className={`flex items-center justify-center p-2 rounded-xl transition-all duration-200 shadow-md ${
                isSendDisabled
                  ? 'bg-dark-800 text-slate-600 cursor-not-allowed border border-white/[0.04]'
                  : 'bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white shadow-brand-500/25 active:scale-95'
              }`}
              title="Send message"
            >
              <Send className={`w-4 h-4 ${isLoading ? 'animate-pulse' : ''}`} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
