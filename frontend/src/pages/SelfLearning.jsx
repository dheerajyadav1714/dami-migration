import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrainCircuit, TrendingUp, Lightbulb, Zap, RefreshCw, MessageSquare, Send, Loader2, BookOpen, CheckCircle2 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, PieChart, Pie } from 'recharts';

const TYPE_COLORS = { correction: '#ef4444', pattern: '#6366f1', optimization: '#10b981', insight: '#f59e0b' };
const AGENT_NAMES = ['risk_scorer', 'architecture_designer', 'wave_planner', 'iac_generator', 'discovery'];

export default function SelfLearning() {
  const [stats, setStats] = useState(null);
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFeedback, setShowFeedback] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [feedback, setFeedback] = useState({ agent_name: 'risk_scorer', learning_type: 'correction', original_output: '', corrected_output: '' });

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      axios.get('http://localhost:8000/api/learning/stats').catch(() => ({ data: {} })),
      axios.get('http://localhost:8000/api/learning/memories').catch(() => ({ data: [] })),
    ]).then(([sRes, mRes]) => {
      setStats(sRes.data || {});
      setMemories(mRes.data || []);
    }).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const submitFeedback = async () => {
    if (!feedback.corrected_output.trim()) return;
    setSubmitting(true);
    try {
      await axios.post('http://localhost:8000/api/learning/feedback', {
        agent_name: feedback.agent_name,
        learning_type: feedback.learning_type,
        context: {},
        original_output: feedback.original_output,
        corrected_output: feedback.corrected_output,
      });
      setSubmitted(true);
      setFeedback({ agent_name: 'risk_scorer', learning_type: 'correction', original_output: '', corrected_output: '' });
      setTimeout(() => { setSubmitted(false); setShowFeedback(false); fetchData(); }, 2000);
    } catch {
    } finally { setSubmitting(false); }
  };

  // Chart data from stats
  const typeData = stats ? [
    { name: 'Corrections', value: stats.corrections || 0 },
    { name: 'Patterns', value: stats.patterns || 0 },
    { name: 'Optimizations', value: stats.optimizations || 0 },
    { name: 'Insights', value: stats.insights || 0 },
  ].filter(d => d.value > 0) : [];

  // Agent breakdown from memories
  const agentData = {};
  memories.forEach(m => { agentData[m.agent_name] = (agentData[m.agent_name] || 0) + 1; });
  const agentChartData = Object.entries(agentData).map(([name, count]) => ({ name, count }));

  if (loading) return <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full"><div className="text-indigo-400 text-xl font-bold animate-pulse">Loading Self-Learning Data...</div></main>;

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Self-Learning Engine</h1>
          <p className="text-slate-400 font-medium">Track how D.A.M.I.'s AI agents improve over time — learning from human corrections, migration patterns, and feedback loops.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setShowFeedback(!showFeedback)} className="flex items-center gap-2 px-4 py-2.5 text-sm font-bold bg-indigo-600 border border-indigo-500/30 rounded-xl hover:bg-indigo-500 text-white transition-all shadow-lg">
            <MessageSquare className="w-4 h-4" /> Submit Feedback
          </button>
          <button onClick={fetchData} className="flex items-center gap-2 px-4 py-2.5 text-sm font-bold bg-slate-800 border border-white/10 rounded-xl hover:bg-slate-700 text-slate-300 transition-all">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* Feedback Form */}
      {showFeedback && (
        <div className="bg-indigo-500/5 rounded-xl p-6 border border-indigo-500/20 mb-8">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-indigo-400" />
            {submitted ? '✅ Feedback Stored Successfully!' : 'Submit a Correction / Learning'}
          </h3>
          {!submitted && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 font-bold mb-1 block">Agent</label>
                  <select value={feedback.agent_name} onChange={e => setFeedback(p => ({...p, agent_name: e.target.value}))} className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white">
                    {AGENT_NAMES.map(a => <option key={a} value={a}>{a}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-bold mb-1 block">Type</label>
                  <select value={feedback.learning_type} onChange={e => setFeedback(p => ({...p, learning_type: e.target.value}))} className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white">
                    <option value="correction">Correction</option><option value="pattern">Pattern</option><option value="optimization">Optimization</option><option value="insight">Insight</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-400 font-bold mb-1 block">What the agent originally said</label>
                <textarea value={feedback.original_output} onChange={e => setFeedback(p => ({...p, original_output: e.target.value}))} placeholder="e.g. 'Recommended Rehost for Oracle DB'" rows={2} className="w-full bg-[#0b0f19] border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 resize-none" />
              </div>
              <div>
                <label className="text-xs text-slate-400 font-bold mb-1 block">What it should have said (your correction)</label>
                <textarea value={feedback.corrected_output} onChange={e => setFeedback(p => ({...p, corrected_output: e.target.value}))} placeholder="e.g. 'Oracle should be Replatform to AlloyDB due to licensing'" rows={2} className="w-full bg-[#0b0f19] border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 resize-none" />
              </div>
              <button onClick={submitFeedback} disabled={submitting || !feedback.corrected_output.trim()} className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl transition-all">
                {submitting ? <><Loader2 className="w-4 h-4 animate-spin" /> Storing...</> : <><Send className="w-4 h-4" /> Store Learning</>}
              </button>
            </div>
          )}
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="flex items-center justify-between mb-2"><span className="text-sm text-slate-400">Total Memories</span><BrainCircuit className="w-5 h-5 text-indigo-400" /></div>
          <div className="text-4xl font-black text-indigo-400">{stats?.total_memories || 0}</div>
          <div className="text-xs text-slate-500 mt-1">Stored in BigQuery</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="flex items-center justify-between mb-2"><span className="text-sm text-slate-400">Times Applied</span><Zap className="w-5 h-5 text-emerald-400" /></div>
          <div className="text-4xl font-bold text-emerald-400">{stats?.total_applications || 0}</div>
          <div className="text-xs text-slate-500 mt-1">Used in agent prompts</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="flex items-center justify-between mb-2"><span className="text-sm text-slate-400">Avg Effectiveness</span><TrendingUp className="w-5 h-5 text-amber-400" /></div>
          <div className="text-4xl font-bold text-amber-400">{((stats?.avg_effectiveness || 0) * 100).toFixed(0)}%</div>
          <div className="text-xs text-slate-500 mt-1">Based on outcome tracking</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="flex items-center justify-between mb-2"><span className="text-sm text-slate-400">Agents Learning</span><BookOpen className="w-5 h-5 text-blue-400" /></div>
          <div className="text-4xl font-bold text-blue-400">{stats?.agents_learning || 0}</div>
          <div className="text-xs text-slate-500 mt-1">Unique agents with memories</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-lg font-bold text-white mb-4">Learning Type Distribution</h3>
          <div className="h-[250px]">
            {typeData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart><Pie data={typeData} cx="50%" cy="50%" innerRadius={50} outerRadius={100} paddingAngle={3} dataKey="value" label={({name, percent}) => `${name} ${(percent*100).toFixed(0)}%`}>
                  {typeData.map((e, i) => <Cell key={i} fill={Object.values(TYPE_COLORS)[i]} />)}
                </Pie><Tooltip contentStyle={{backgroundColor:'#0f172a', borderColor:'#1e293b', color:'#fff'}} /></PieChart>
              </ResponsiveContainer>
            ) : <div className="flex items-center justify-center h-full text-slate-500">No data yet</div>}
          </div>
        </div>
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-lg font-bold text-white mb-4">Memories by Agent</h3>
          <div className="h-[250px]">
            {agentChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={agentChartData}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" /><XAxis dataKey="name" stroke="#64748b" tick={{fontSize:10}} /><YAxis stroke="#64748b" tick={{fontSize:11}} /><Tooltip contentStyle={{backgroundColor:'#0f172a', borderColor:'#1e293b', color:'#fff'}} /><Bar dataKey="count" fill="#6366f1" radius={[4,4,0,0]} /></BarChart>
              </ResponsiveContainer>
            ) : <div className="flex items-center justify-center h-full text-slate-500">No data yet</div>}
          </div>
        </div>
      </div>

      {/* Memory Table */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><Lightbulb className="w-5 h-5 text-amber-400" /> Stored Memories ({memories.length})</h3>
        <div className="space-y-3 max-h-[500px] overflow-y-auto custom-scrollbar">
          {memories.map((m, i) => (
            <div key={i} className="p-4 bg-slate-900/30 rounded-xl border border-white/5 hover:bg-white/[0.02] transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold bg-slate-800 text-slate-300 px-2 py-0.5 rounded">{m.agent_name}</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full`} style={{ background: `${TYPE_COLORS[m.learning_type]}15`, color: TYPE_COLORS[m.learning_type] }}>{m.learning_type}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-slate-500">Applied {m.applied_count}x</span>
                  <span className="text-xs font-bold text-emerald-400">{((m.effectiveness_score || 0) * 100).toFixed(0)}%</span>
                </div>
              </div>
              {m.corrected_output && <p className="text-xs text-white mb-1"><strong className="text-emerald-400">✅ Correction:</strong> {m.corrected_output}</p>}
              {m.original_output && <p className="text-[10px] text-slate-500"><strong>Original:</strong> {m.original_output}</p>}
              {m.tags && m.tags.length > 0 && (
                <div className="flex gap-1 mt-2">{m.tags.map((t, j) => <span key={j} className="text-[9px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">{t}</span>)}</div>
              )}
            </div>
          ))}
          {memories.length === 0 && <div className="text-center text-slate-500 p-8">No memories stored yet. Submit feedback above to start learning!</div>}
        </div>
      </div>
    </main>
  );
}
