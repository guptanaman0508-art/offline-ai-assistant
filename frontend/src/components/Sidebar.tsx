import React from 'react';
import { Plus, Clock } from 'lucide-react';

export const Sidebar: React.FC = () => {
  // Placeholder data – in a real app this would come from backend/history store
  const recentConversations = [
    { id: 'c1', title: 'Study notes' },
    { id: 'c2', title: 'Research paper summary' },
    { id: 'c3', title: 'Programming help' },
  ];

  return (
    <aside className="hidden md:flex flex-col w-64 h-full bg-dark-900/95 border-r border-white/[0.04] p-4">
      {/* Branding */}
      <div className="flex items-center gap-2 mb-6">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-indigo-400 flex items-center justify-center text-white shadow-lg shadow-brand-500/20">
          <Plus className="w-5 h-5" />
        </div>
        <h2 className="text-lg font-semibold text-white tracking-wide">Offline AI Assistant</h2>
      </div>

      {/* New Chat button */}
      <button className="flex items-center gap-2 px-3 py-2 mb-4 rounded-xl bg-dark-850 hover:bg-dark-800 text-slate-300 hover:text-white transition-colors">
        <Plus className="w-4 h-4" />
        New Chat
      </button>

      {/* Conversation history */}
      <div className="flex-1 overflow-y-auto">
        <h3 className="text-xs font-medium text-slate-400 uppercase mb-2">Recent</h3>
        <ul className="space-y-1">
          {recentConversations.map((c) => (
            <li key={c.id} className="px-2 py-1 rounded hover:bg-dark-800 cursor-pointer text-slate-300 hover:text-white transition-colors">
              {c.title}
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
};

