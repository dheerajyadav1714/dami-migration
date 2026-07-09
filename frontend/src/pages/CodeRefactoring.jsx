import React, { useState } from 'react';
import api from '../lib/api';
import axios from 'axios';
import { Code, Send, Bot, User, Copy, Check } from 'lucide-react';

export default function CodeRefactoring() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "I'm the D.A.M.I. Code Refactoring Agent powered by Gemini. Paste your legacy application code (Java, .NET, Python, etc.) and I'll analyze it and suggest GCP-native refactoring — Cloud Run, GKE containers, Cloud Functions, Pub/Sub integrations, and more." }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(null);

  const suggestions = [
    "Refactor this Java monolith for Cloud Run",
    "Convert this Windows service to a containerized GKE workload",
    "Migrate this .NET app to use Cloud SQL instead of on-prem SQL Server",
    "Add Cloud Pub/Sub messaging to replace RabbitMQ",
  ];

  const sendMessage = async (text) => {
    if (!text.trim()) return;
    setMessages(prev => [...prev, { role: 'user', text: text.trim() }]);
    setInput('');
    setLoading(true);
    try {
      const prompt = `You are a cloud migration code refactoring expert. Analyze the following and provide GCP-native refactored code with explanations:\n\n${text.trim()}`;
      const res = await api.post('/api/chat', { prompt });
      setMessages(prev => [...prev, { role: 'assistant', text: res.data?.reply || 'No response.' }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Error contacting the AI agent. Ensure the backend is running.' }]);
    } finally {
      setLoading(false);
    }
  };

  const copyText = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopied(idx);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-hidden relative z-10">
      <header className="p-10 pb-4">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Code Refactoring Agent</h1>
        <p className="text-slate-400 font-medium">AI-powered code transformation — paste legacy code and get GCP-native refactored output.</p>
        <div className="h-px bg-white/10 w-full mt-6" />
      </header>

      <div className="flex-1 overflow-y-auto px-10 py-4 space-y-4 custom-scrollbar">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && <div className="w-8 h-8 rounded-full bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center shrink-0 mt-1"><Code className="w-4 h-4 text-emerald-400" /></div>}
            <div className={`max-w-[75%] p-4 rounded-2xl text-sm leading-relaxed relative group ${msg.role === 'user' ? 'bg-indigo-600/20 border border-indigo-500/30' : 'bg-[#131826] border border-white/[0.05]'}`}>
              <pre className="whitespace-pre-wrap font-mono text-xs">{msg.text}</pre>
              {msg.role === 'assistant' && i > 0 && (
                <button onClick={() => copyText(msg.text, i)} className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1.5 rounded-lg bg-slate-800 border border-white/10 text-slate-400 hover:text-white transition-all">
                  {copied === i ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              )}
            </div>
            {msg.role === 'user' && <div className="w-8 h-8 rounded-full bg-slate-700 border border-white/10 flex items-center justify-center shrink-0 mt-1"><User className="w-4 h-4 text-slate-300" /></div>}
          </div>
        ))}
        {loading && <div className="flex gap-3"><div className="w-8 h-8 rounded-full bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center shrink-0"><Code className="w-4 h-4 text-emerald-400" /></div><div className="bg-[#131826] border border-white/[0.05] p-4 rounded-2xl"><div className="flex gap-1"><span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" /><span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{animationDelay:'0.1s'}} /><span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{animationDelay:'0.2s'}} /></div></div></div>}
      </div>

      {messages.length <= 1 && <div className="px-10 pb-2"><div className="flex flex-wrap gap-2">{suggestions.map((s, i) => <button key={i} onClick={() => sendMessage(s)} className="text-xs bg-[#131826] border border-white/10 text-slate-300 px-3 py-2 rounded-lg hover:bg-emerald-600/10 hover:border-emerald-500/30 hover:text-white transition-all">{s}</button>)}</div></div>}

      <div className="p-6 px-10 border-t border-white/5">
        <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
          placeholder="Paste your legacy code here or describe what you want to refactor..." disabled={loading} rows={3}
          className="w-full bg-[#131826] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 disabled:opacity-50 font-mono resize-none mb-3" />
        <button onClick={() => sendMessage(input)} disabled={loading || !input.trim()} className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-6 py-2.5 rounded-xl transition-colors shadow-lg flex items-center gap-2 font-bold text-sm">
          <Send className="w-4 h-4" /> Refactor Code
        </button>
      </div>
    </main>
  );
}
