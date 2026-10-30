import React from 'react';
import { Sparkles, MessageSquare, ShieldCheck, Zap, ArrowRight } from 'lucide-react';

interface EmptyStateProps {
  selectedModel: string;
  onSelectPrompt: (promptText: string) => void;
}

const STARTER_PROMPTS = [
  {
    title: 'Explain Binary Search',
    subtitle: 'Concept breakdown with time complexity',
    prompt: 'Explain Binary Search in 3 clear bullet points. Mention its time complexity.',
  },
  {
    title: 'Process vs Thread',
    subtitle: 'Operating systems memory & context switching',
    prompt: 'What is the difference between a process and a thread in an operating system? Answer in 3 sentences.',
  },
  {
    title: 'ACID Properties',
    subtitle: 'Relational database transaction principles',
    prompt: 'Summarize what the ACID properties stand for in relational database management systems.',
  },
  {
    title: 'Generate Exam Question',
    subtitle: 'Multiple-choice question with answer key',
    prompt: 'Generate a single multiple-choice exam question testing understanding of stack vs queue data structures, including 4 options (A-D) and the correct answer with an explanation.',
  },
];

export const EmptyState: React.FC<EmptyStateProps> = ({
  selectedModel,
  onSelectPrompt,
}) => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto my-auto animate-fade-in">
      {/* Icon Graphic */}
      <div className="relative mb-6">
        <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-gradient-to-tr from-brand-600/30 via-indigo-600/20 to-purple-600/30 border border-brand-500/30 flex items-center justify-center shadow-2xl shadow-brand-500/20 backdrop-blur-sm">
          <Sparkles className="w-8 h-8 sm:w-10 sm:h-10 text-brand-400" />
        </div>
        <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 ring-4 ring-dark-950 animate-pulse-subtle"></span>
      </div>

      {/* Main Heading */}
      <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
        How can I help your studies today?
      </h2>
      <p className="text-sm sm:text-base text-slate-400 mb-8 max-w-lg leading-relaxed">
        Running 100% locally on your machine with{' '}
        <span className="text-indigo-400 font-medium">{selectedModel || 'local LLM'}</span>. Your
        prompts and lecture notes never leave this computer.
      </p>

      {/* Quick Feature Badges */}
      <div className="flex flex-wrap items-center justify-center gap-2.5 sm:gap-4 mb-8 text-xs text-slate-400">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-dark-900 border border-white/[0.06]">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Zero cloud telemetry</span>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-dark-900 border border-white/[0.06]">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>Apple Silicon hardware acceleration</span>
        </div>
      </div>

      {/* Starter Prompts Grid */}
      <div className="w-full text-left">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 px-1 flex items-center gap-1.5">
          <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
          <span>Academic Starter Prompts</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full">
          {STARTER_PROMPTS.map((item, idx) => (
            <button
              key={idx}
              onClick={() => onSelectPrompt(item.prompt)}
              className="group flex flex-col p-3.5 rounded-xl bg-dark-900/60 hover:bg-dark-850 border border-white/[0.06] hover:border-brand-500/40 text-left transition-all duration-200 shadow-sm hover:shadow-lg hover:shadow-brand-500/5 active:scale-[0.99]"
            >
              <div className="flex items-center justify-between w-full mb-1">
                <span className="text-sm font-medium text-slate-200 group-hover:text-brand-300 transition-colors">
                  {item.title}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-brand-400 group-hover:translate-x-0.5 transition-all" />
              </div>
              <span className="text-xs text-slate-400 line-clamp-1">{item.subtitle}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
