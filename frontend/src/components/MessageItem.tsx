import React from 'react';
import { Bot, User, Clock, AlertCircle, Copy, Check } from 'lucide-react';
import { ChatMessage } from '../types/api';

interface MessageItemProps {
  message: ChatMessage;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`flex w-full gap-3 sm:gap-4 p-4 sm:p-5 transition-colors duration-200 ${
        isUser
          ? 'bg-transparent justify-end'
          : message.isError
          ? 'bg-rose-950/20 border-y border-rose-900/30'
          : 'bg-dark-900/60 border-y border-white/[0.04]'
      }`}
    >
      <div
        className={`flex w-full max-w-3xl gap-3 sm:gap-4 ${
          isUser ? 'flex-row-reverse' : 'flex-row'
        }`}
      >
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-8 h-8 sm:w-9 sm:h-9 rounded-xl flex items-center justify-center shadow-lg ${
            isUser
              ? 'bg-gradient-to-tr from-brand-600 to-indigo-500 text-white shadow-brand-500/20'
              : message.isError
              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
              : 'bg-dark-800 text-indigo-400 border border-white/10 shadow-black/40'
          }`}
        >
          {isUser ? (
            <User className="w-4 h-4 sm:w-5 sm:h-5" />
          ) : message.isError ? (
            <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5" />
          ) : (
            <Bot className="w-4 h-4 sm:w-5 sm:h-5" />
          )}
        </div>

        {/* Bubble & Metadata */}
        <div className={`flex flex-col flex-1 min-w-0 ${isUser ? 'items-end' : 'items-start'}`}>
          <div className="flex items-center gap-2 mb-1 text-xs text-slate-400 px-1">
            <span className="font-medium text-slate-300">
              {isUser ? 'You' : message.model || 'Offline Assistant'}
            </span>
            <span>•</span>
            <span className="text-slate-500">{message.timestamp}</span>

            {!isUser && message.latencySeconds !== undefined && (
              <span className="inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded-md bg-white/[0.06] text-indigo-300 border border-white/[0.06]">
                <Clock className="w-3 h-3 text-indigo-400" />
                {message.latencySeconds.toFixed(2)}s
              </span>
            )}
          </div>

          <div
            className={`relative group rounded-2xl px-4 py-3 sm:px-5 sm:py-3.5 text-sm sm:text-base leading-relaxed ${
              isUser
                ? 'bg-gradient-to-r from-brand-600 to-indigo-600 text-white rounded-tr-sm shadow-md shadow-brand-600/10'
                : message.isError
                ? 'bg-rose-900/30 text-rose-200 border border-rose-800/40 rounded-tl-sm'
                : 'bg-dark-850/80 text-slate-100 border border-white/[0.07] rounded-tl-sm shadow-sm'
            }`}
          >
            <div className="whitespace-pre-wrap break-words">{message.content}</div>

            {/* Action Bar (Copy Button) */}
            {!isUser && !message.isError && (
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded-lg bg-dark-800/80 hover:bg-dark-700 text-slate-400 hover:text-white border border-white/10 transition-colors shadow-sm"
                  title="Copy response"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
