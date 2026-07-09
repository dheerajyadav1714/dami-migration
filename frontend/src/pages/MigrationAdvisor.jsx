import React, { useState } from 'react';
import axios from 'axios';
import { MessageSquare, Send, Bot, User, Sparkles } from 'lucide-react';

export default function MigrationAdvisor() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hello! I'm the D.A.M.I. Migration Advisor powered by Gemini. Ask me anything about your migration — risk strategies, wave sequencing, architecture decisions, or compliance requirements." }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const suggestions = [
    "What's the best migration strategy for our Oracle database?",
    "How should we sequence Wave 2 to minimize downtime?",
    "What GCP services map to our Redis cache?",
    "Explain the risk factors for our payment application",
  ];

  const sendMessage = async (text) => {
    if (!text.trim()) return;
    const userMsg = { role: 'user', text: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post('http://localhost:8000/api/chat', { prompt: text.trim() });
      setMessages(prev => [...prev, { role: 'assistant', text: res.data?.reply || 'No response received.' }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Sorry, I encountered an error. Please ensure the backend is running.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-hidden relative z-10">
      <header className="p-10 pb-4">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Migration Advisor</h1>
        <p className="text-slate-400 font-medium">AI-powered migration guidance using Gemini — ask questions about your infrastructure, strategies, and migration plan.</p>
        <div className="h-px bg-white/10 w-full mt-6" />
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-10 py-4 space-y-4 custom-scrollbar">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-4 h-4 text-indigo-400" />
              </div>
            )}
            <div className={`max-w-[70%] p-4 rounded-2xl text-sm leading-relaxed ${
              msg.role === 'user' ? 'bg-indigo-600/20 border border-indigo-500/30 text-white' : 'bg-[#131826] border border-white/[0.05] text-slate-200'
            }`}>
              <pre className="whitespace-pre-wrap font-sans">{msg.text}</pre>
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-slate-700 border border-white/10 flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4 text-slate-300" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0"><Bot className="w-4 h-4 text-indigo-400" /></div>
            <div className="bg-[#131826] border border-white/[0.05] p-4 rounded-2xl"><div className="flex gap-1"><span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" /><span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay:'0.1s'}} /><span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay:'0.2s'}} /></div></div>
          </div>
        )}
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="px-10 pb-2">
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s, i) => (
              <button key={i} onClick={() => sendMessage(s)} className="text-xs bg-[#131826] border border-white/10 text-slate-300 px-3 py-2 rounded-lg hover:bg-indigo-600/20 hover:border-indigo-500/30 hover:text-white transition-all flex items-center gap-1.5">
                <Sparkles className="w-3 h-3 text-indigo-400" /> {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-6 px-10 border-t border-white/5">
        <div className="flex gap-3">
          <input type="text" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage(input)}
            placeholder="Ask about your migration..." disabled={loading}
            className="flex-1 bg-[#131826] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50" />
          <button onClick={() => sendMessage(input)} disabled={loading || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white p-3 rounded-xl transition-colors shadow-lg">
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </main>
  );
}
