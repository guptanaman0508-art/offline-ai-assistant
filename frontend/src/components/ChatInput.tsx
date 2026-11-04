import React, { useRef, useEffect, useState } from 'react';
import { Send, CornerDownLeft, Paperclip } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isLoading: boolean;
  disabled?: boolean;
  // New props for file handling
  selectedFile?: File | null;
  onFileSelect: (file: File | null) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSend,
  isLoading,
  disabled = false,
  selectedFile = null,
  onFileSelect,
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
      if (!isLoading && !disabled && (value.trim() || selectedFile)) {
        onSend();
      }
    }
  };

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    onFileSelect(file);
    // Reset the input value to allow re-selecting the same file if removed
    e.target.value = '';
  };

  const handleRemoveFile = () => {
    onFileSelect(null);
  };

  const isSendDisabled = disabled || isLoading || (!value.trim() && !selectedFile);

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

        {/* File attachment preview */}
        {selectedFile && (
          <div className="flex items-center gap-2 px-4 py-2 bg-dark-800/60 border-t border-white/[0.04]">
            <span className="text-sm text-slate-300 truncate" title={selectedFile.name}>
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </span>
            <button
              type="button"
              onClick={handleRemoveFile}
              className="p-1 text-slate-400 hover:text-white"
              title="Remove attachment"
            >
              ✕
            </button>
          </div>
        )}

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

          <div className="ml-auto flex items-center gap-2">
            {/* Paperclip button */}
            <button
              type="button"
              onClick={triggerFileSelect}
              disabled={isLoading || disabled}
              className="p-2 rounded hover:bg-dark-800/40 text-slate-400 hover:text-white"
              title="Attach a document (PDF, TXT, DOCX)"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <input
              type="file"
              accept=".pdf,.txt,.docx"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
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