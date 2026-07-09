import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Bot, User, Plus, Download, Send, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ConversationalAssistant() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: "Hello! I'm D.A.M.I., your Autonomous Migration Intelligence agent. I have full access to your discovery data, migration wave plans, and architecture configurations. How can I help you today?"
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    // Fetch dynamic suggestions on mount
    axios.get('http://localhost:8000/api/chat/suggestions')
      .then(res => setSuggestions(res.data.suggestions || []))
      .catch(err => console.error("Failed to load suggestions", err));
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { id: Date.now(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/chat', { prompt: userMessage.content });
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.reply || "I'm sorry, I couldn't process that request."
      }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: "Oops! My backend AI orchestration service is currently unavailable. Please ensure the FastAPI server is running."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestion = (text) => {
    setInput(text);
  };

  const handleExport = () => {
    let transcript = "D.A.M.I. Conversational Assistant - Chat Transcript\n";
    transcript += "========================================================\n\n";
    
    messages.forEach(msg => {
        const role = msg.role === 'assistant' ? 'D.A.M.I. AI' : 'User';
        transcript += `[${role}]\n${msg.content}\n\n`;
    });

    const blob = new Blob([transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dami-chat-transcript-${new Date().toISOString().slice(0,10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <main className="flex-1 flex flex-col h-full overflow-hidden relative z-10 p-6 pb-0">
        {/* Header */}
        <header className="flex items-center justify-between pb-6 shrink-0 border-b border-white/10">
            <div>
                <h2 className="text-3xl font-extrabold tracking-tight text-white drop-shadow-md">Conversational Assistant</h2>
                <p className="text-slate-400 mt-1 font-medium">Chat directly with the D.A.M.I. AI regarding your cloud migration.</p>
            </div>
            <div className="flex items-center gap-3">
                <button 
                  onClick={() => setMessages([messages[0]])}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold bg-slate-800/70 border border-slate-700/80 hover:bg-slate-700/70 text-slate-300 hover:text-white transition-all shadow-md hover:shadow-lg"
                >
                    <Plus className="w-4 h-4" />
                    New Chat
                </button>
                <button 
                  onClick={handleExport}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold bg-indigo-600 border border-indigo-500/50 hover:bg-indigo-500 text-white transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)] hover:scale-105 active:scale-95">
                    <Download className="w-4 h-4" />
                    Export
                </button>
            </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 custom-scrollbar">
            {messages.map((msg, index) => (
              <div key={msg.id} className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : 'max-w-4xl'}`}>
                  {msg.role === 'assistant' && (
                    <div className="w-10 h-10 shrink-0 flex items-center justify-center bg-indigo-500/20 rounded-full border border-indigo-500/40 shadow-[0_0_10px_rgba(79,70,229,0.3)]">
                        <Bot className="w-5 h-5 text-indigo-400" />
                    </div>
                  )}
                  
                  <div className={`p-4 rounded-2xl ${msg.role === 'user' ? 'bg-indigo-600 border border-indigo-500/50 shadow-lg text-white max-w-2xl' : 'glass-card w-full shadow-md'}`}>
                      {msg.role === 'assistant' && <p className="font-bold text-slate-200 mb-2">D.A.M.I. AI</p>}
                      {msg.role === 'assistant' ? (
                        <div className="prose prose-invert max-w-none prose-p:text-slate-300 prose-headings:text-slate-200 prose-a:text-indigo-400 prose-code:text-indigo-300 prose-pre:bg-slate-900/80 prose-pre:border prose-pre:border-slate-700 prose-table:w-full prose-table:border-collapse prose-th:border prose-th:border-slate-700 prose-th:bg-slate-800/80 prose-th:px-4 prose-th:py-2 prose-td:border prose-td:border-slate-700/80 prose-td:px-4 prose-td:py-2 prose-tr:bg-slate-800/20 even:prose-tr:bg-slate-800/40">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap text-white font-medium">{msg.content}</p>
                      )}
                      
                      {msg.role === 'assistant' && index === 0 && suggestions.length > 0 && (
                        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3">
                            {suggestions.map((suggestion, idx) => (
                                <button key={idx} onClick={() => handleSuggestion(suggestion.text)} className="glass-card text-left p-3 rounded-xl hover:border-indigo-500/50 transition-colors border border-white/5 flex items-center gap-3">
                                    <span className="text-xl">{suggestion.icon}</span>
                                    <p className="text-sm font-bold text-slate-200">{suggestion.text}</p>
                                </button>
                            ))}
                        </div>
                      )}
                  </div>

                  {msg.role === 'user' && (
                    <div className="w-10 h-10 shrink-0 flex items-center justify-center bg-slate-700/50 rounded-full border border-slate-600 shadow-md">
                        <User className="w-5 h-5 text-slate-300" />
                    </div>
                  )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex items-start gap-4 max-w-4xl">
                  <div className="w-10 h-10 shrink-0 flex items-center justify-center bg-indigo-500/20 rounded-full border border-indigo-500/40">
                      <Bot className="w-5 h-5 text-indigo-400" />
                  </div>
                  <div className="glass-card rounded-2xl p-4 w-32 flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                      <span className="text-sm font-medium text-slate-400">Thinking...</span>
                  </div>
              </div>
            )}
            <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 shrink-0 bg-slate-900/50 backdrop-blur-md border-t border-white/10 rounded-t-3xl shadow-[0_-10px_40px_rgba(0,0,0,0.3)]">
            <form onSubmit={handleSend} className="max-w-5xl mx-auto relative flex items-end gap-4 bg-slate-800/50 p-2 pl-6 border border-slate-700/80 rounded-2xl shadow-inner focus-within:border-indigo-500/50 focus-within:ring-1 focus-within:ring-indigo-500/30 transition-all">
                <textarea 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend(e);
                    }
                  }}
                  placeholder="Ask D.A.M.I. anything about your migration..."
                  className="w-full bg-transparent border-none text-white placeholder:text-slate-500 focus:outline-none py-3 max-h-32 min-h-[44px] resize-none font-medium custom-scrollbar"
                  rows="1"
                />
                <button 
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="shrink-0 p-3 bg-indigo-600 rounded-xl hover:bg-indigo-500 transition-all text-white disabled:opacity-50 disabled:hover:bg-indigo-600 shadow-md hover:shadow-lg disabled:shadow-none mb-1 mr-1"
                >
                  <Send className="w-5 h-5" />
                </button>
            </form>
            <div className="max-w-5xl mx-auto text-center mt-3">
              <span className="text-xs text-slate-500 font-medium">D.A.M.I. AI agents may hallucinate. Verify critical IaC and infrastructure configurations before deployment.</span>
            </div>
        </div>
    </main>
  );
}
