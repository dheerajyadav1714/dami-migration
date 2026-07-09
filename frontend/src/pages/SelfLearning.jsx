import React, { useState, useMemo } from 'react';
import { BrainCircuit, TrendingUp, BookOpen, Lightbulb, BarChart3 } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const LEARNING_DATA = [
  { week: 'W1', accuracy: 72, decisions: 15, improvements: 3 },
  { week: 'W2', accuracy: 78, decisions: 28, improvements: 5 },
  { week: 'W3', accuracy: 82, decisions: 42, improvements: 7 },
  { week: 'W4', accuracy: 87, decisions: 61, improvements: 4 },
  { week: 'W5', accuracy: 89, decisions: 78, improvements: 6 },
  { week: 'W6', accuracy: 93, decisions: 95, improvements: 3 },
];

const LEARNINGS = [
  { title: 'Oracle DB Migration Pattern', desc: 'Learned that Oracle DBs with custom TNS config should use Bare Metal Solution, not Cloud SQL.', category: 'Architecture', confidence: 94, date: '2026-06-15' },
  { title: 'Windows 2008 R2 EOL Risk', desc: 'Auto-flagged all Windows 2008 R2 servers as critical license risk — confirmed by compliance team.', category: 'Compliance', confidence: 98, date: '2026-06-18' },
  { title: 'Redis Cache Sizing', desc: 'Learned that Memorystore for Redis requires 2x on-prem memory allocation for optimal performance.', category: 'Sizing', confidence: 89, date: '2026-06-22' },
  { title: 'Payment App Dependencies', desc: 'Discovered hidden dependency between payment app and LDAP server through network flow analysis.', category: 'Dependencies', confidence: 91, date: '2026-06-25' },
  { title: 'Wave Sequencing Optimization', desc: 'Learned that migrating load balancers before web servers reduces cutover downtime by 40%.', category: 'Wave Planning', confidence: 86, date: '2026-07-01' },
];

export default function SelfLearning() {
  const currentAccuracy = LEARNING_DATA[LEARNING_DATA.length - 1].accuracy;
  const totalDecisions = LEARNING_DATA.reduce((s, d) => s + d.decisions, 0);
  const totalImprovements = LEARNING_DATA.reduce((s, d) => s + d.improvements, 0);

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Self-Learning Engine</h1>
        <p className="text-slate-400 font-medium">Track how D.A.M.I.'s AI agents improve over time — learning from migration decisions, feedback loops, and historical patterns.</p>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Current Accuracy</div>
          <div className="text-4xl font-black text-emerald-400">{currentAccuracy}%</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Total Decisions Made</div>
          <div className="text-4xl font-bold text-white">{totalDecisions}</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Pattern Improvements</div>
          <div className="text-4xl font-bold text-indigo-400">{totalImprovements}</div>
        </div>
      </div>

      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg mb-8">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><TrendingUp className="w-5 h-5 text-emerald-400" /> Learning Curve</h3>
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={LEARNING_DATA}>
              <defs><linearGradient id="colorAcc" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} /><stop offset="95%" stopColor="#6366f1" stopOpacity={0} /></linearGradient></defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="week" stroke="#64748b" tick={{fontSize:11}} />
              <YAxis domain={[60, 100]} stroke="#64748b" tick={{fontSize:11}} />
              <Tooltip contentStyle={{backgroundColor:'#0f172a', borderColor:'#1e293b', color:'#fff'}} />
              <Area type="monotone" dataKey="accuracy" stroke="#6366f1" fill="url(#colorAcc)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><Lightbulb className="w-5 h-5 text-amber-400" /> Learned Patterns</h3>
        <div className="space-y-3">
          {LEARNINGS.map((l, i) => (
            <div key={i} className="p-4 bg-slate-900/30 rounded-xl border border-white/5 hover:bg-white/[0.02] transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="font-bold text-white text-sm">{l.title}</div>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded-full">{l.category}</span>
                  <span className="text-xs font-bold text-emerald-400">{l.confidence}%</span>
                </div>
              </div>
              <p className="text-xs text-slate-400">{l.desc}</p>
              <div className="text-[10px] text-slate-500 mt-2">{l.date}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
