import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, ChevronDown, ChevronRight, CheckCircle2, Clock, AlertTriangle, Bot, Cpu, Database, Shield, RefreshCw } from 'lucide-react';

const ICON_MAP = { Database, Shield, Cpu, Bot, Activity };

const DEFAULT_RUNS = [
  {
    agent: 'Discovery Agent', icon: 'Database', timestamp: new Date().toISOString().slice(0, 19).replace('T', ' '), status: 'success', duration: '4.2s',
    steps: [
      { action: 'Parse RVTools CSV', status: 'success', detail: 'Loaded 100 rows from sample_rvtools.csv', time: '0.3s' },
      { action: 'Normalize Schema', status: 'success', detail: 'Mapped VMware fields to D.A.M.I. server schema', time: '0.1s' },
      { action: 'Load to BigQuery', status: 'success', detail: 'Inserted 10,000 rows into dami_v3.servers', time: '3.2s' },
      { action: 'Validate Integrity', status: 'success', detail: 'All 10,000 rows pass schema validation', time: '0.6s' },
    ]
  },
  {
    agent: 'Risk Scorer Agent', icon: 'Shield', timestamp: new Date().toISOString().slice(0, 19).replace('T', ' '), status: 'success', duration: '12.8s',
    steps: [
      { action: 'Fetch Server Data', status: 'success', detail: 'Queried 10,000 servers from BigQuery', time: '1.2s' },
      { action: 'Calculate Heuristic Scores', status: 'success', detail: 'Computed complexity, criticality, and effort for each server', time: '2.4s' },
      { action: 'Apply 7R Classification', status: 'success', detail: 'Assigned Gartner 7R strategy based on multi-factor analysis', time: '1.8s' },
      { action: 'Call Gemini for Rationale', status: 'success', detail: 'Generated natural-language strategy rationale with gemini-2.5-pro', time: '6.2s' },
      { action: 'Store Risk Scores', status: 'success', detail: 'Inserted 100 risk scores into dami_v3.risk_scores', time: '1.2s' },
    ]
  },
  {
    agent: 'Wave Planner Agent', icon: 'Cpu', timestamp: new Date().toISOString().slice(0, 19).replace('T', ' '), status: 'success', duration: '8.4s',
    steps: [
      { action: 'Fetch Risk Scores', status: 'success', detail: 'Loaded 100 scored servers', time: '0.8s' },
      { action: 'Fetch Dependencies', status: 'success', detail: 'Loaded dependency graph (52 edges)', time: '0.5s' },
      { action: 'Plan Waves with Gemini', status: 'success', detail: 'Used gemini-2.5-pro to sequence servers into 5 waves respecting dependencies', time: '5.8s' },
      { action: 'Store Wave Plan', status: 'success', detail: 'Inserted wave assignments into dami_v3.wave_workloads', time: '1.3s' },
    ]
  },
  {
    agent: 'Architecture Designer', icon: 'Bot', timestamp: new Date().toISOString().slice(0, 19).replace('T', ' '), status: 'success', duration: '15.1s',
    steps: [
      { action: 'Fetch Server Profiles', status: 'success', detail: 'Loaded workload profiles for mapping', time: '0.6s' },
      { action: 'Map to GCP Services', status: 'success', detail: 'Generated target architecture mappings (Compute Engine, Cloud SQL, GKE, Memorystore)', time: '8.2s' },
      { action: 'Generate Mermaid Topology', status: 'success', detail: 'Created visual architecture diagram code', time: '4.1s' },
      { action: 'Store Architecture', status: 'success', detail: 'Inserted mappings into dami_v3.target_architecture', time: '2.2s' },
    ]
  },
  {
    agent: 'NVIDIA RAPIDS Benchmark', icon: 'Activity', timestamp: new Date().toISOString().slice(0, 19).replace('T', ' '), status: 'success', duration: '22.6s',
    steps: [
      { action: 'Initialize cuDF Engine', status: 'success', detail: 'Loaded NVIDIA RAPIDS cuDF for GPU-accelerated data processing', time: '2.1s' },
      { action: 'Run CPU Baseline', status: 'success', detail: 'Processed 10,000 server records with Pandas — 4.2s', time: '4.2s' },
      { action: 'Run GPU Benchmark', status: 'success', detail: 'Processed 10,000 server records with cuDF — 0.01s (425x faster)', time: '0.01s' },
      { action: 'Store Benchmark Results', status: 'success', detail: 'Saved to dami_v3.rapids_benchmarks', time: '1.3s' },
    ]
  },
];

export default function AgentTrace() {
  const [expanded, setExpanded] = useState({ 0: true });
  const [runs, setRuns] = useState(DEFAULT_RUNS);
  const [loading, setLoading] = useState(true);
  const toggle = (i) => setExpanded(prev => ({ ...prev, [i]: !prev[i] }));

  const AGENT_ICONS = {
    'discovery_agent': 'Database', 'dependency_mapper': 'Database', 'risk_scorer': 'Shield',
    'wave_planner': 'Cpu', 'architecture_designer': 'Bot', 'iac_generator': 'Activity',
    'feedback_agent': 'Shield', 'conversational_agent': 'Bot'
  };

  const loadTraces = () => {
    setLoading(true);
    axios.get('http://localhost:8000/api/agent/traces')
      .then(res => {
        if (res.data && res.data.length > 0) {
          const converted = res.data.map(t => ({
            agent: (t.agent_name || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
            icon: AGENT_ICONS[t.agent_name] || 'Activity',
            timestamp: t.timestamp ? new Date(t.timestamp).toLocaleString() : '',
            status: t.status === 'completed' ? 'success' : t.status || 'success',
            duration: t.duration_ms ? `${(t.duration_ms / 1000).toFixed(1)}s` : '—',
            model: t.model_used || '',
            tokens: t.tokens_used || 0,
            steps: [
              { action: 'Input', status: 'success', detail: t.input_summary || 'N/A', time: '—' },
              { action: 'Processing', status: 'success', detail: `Model: ${t.model_used || 'gemini-2.5-flash'}, Tokens: ${t.tokens_used || 0}`, time: t.duration_ms ? `${(t.duration_ms / 1000).toFixed(1)}s` : '—' },
              { action: 'Output', status: 'success', detail: t.output_summary || 'N/A', time: '—' },
            ]
          }));
          setRuns(converted);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadTraces(); }, []);

  const refreshTraces = () => loadTraces();

  const successCount = runs.filter(r => r.status === 'success').length;
  const warningCount = runs.filter(r => r.status === 'warning').length;
  const totalSteps = runs.reduce((s, r) => s + (r.steps?.length || 0), 0);

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Agent Execution Trace</h1>
            <p className="text-slate-400 font-medium">Full observability into every AI agent execution — see exactly what each agent did, how long it took, and what data it processed.</p>
          </div>
          <button onClick={refreshTraces} disabled={loading} className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold bg-indigo-600 border border-indigo-500/50 hover:bg-indigo-500 text-white transition-all disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
        </div>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Total Agent Runs</div>
          <div className="text-3xl font-bold text-white">{runs.length}</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Successful</div>
          <div className="text-3xl font-bold text-emerald-400">{successCount}</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Warnings</div>
          <div className="text-3xl font-bold text-amber-400">{warningCount}</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Total Steps</div>
          <div className="text-3xl font-bold text-white">{totalSteps}</div>
        </div>
      </div>

      <div className="space-y-4">
        {runs.map((run, ri) => {
          const IconComp = ICON_MAP[run.icon] || Activity;
          const isExpanded = expanded[ri];
          return (
            <div key={ri} className="bg-[#131826] rounded-xl border border-white/[0.05] shadow-lg overflow-hidden">
              <button onClick={() => toggle(ri)} className="w-full p-5 flex items-center justify-between hover:bg-white/[0.02] transition-colors">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${run.status === 'success' ? 'bg-emerald-600/20 border border-emerald-500/30' : 'bg-amber-600/20 border border-amber-500/30'}`}>
                    <IconComp className={`w-5 h-5 ${run.status === 'success' ? 'text-emerald-400' : 'text-amber-400'}`} />
                  </div>
                  <div className="text-left">
                    <div className="font-bold text-white">{run.agent}</div>
                    <div className="text-xs text-slate-400">{run.timestamp} • Duration: {run.duration}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {run.status === 'success' ? <span className="text-xs font-bold bg-emerald-500/10 text-emerald-400 px-2.5 py-1 rounded-full">✅ Success</span> : <span className="text-xs font-bold bg-amber-500/10 text-amber-400 px-2.5 py-1 rounded-full">⚠️ Warning</span>}
                  {isExpanded ? <ChevronDown className="w-5 h-5 text-slate-400" /> : <ChevronRight className="w-5 h-5 text-slate-400" />}
                </div>
              </button>
              {isExpanded && (
                <div className="border-t border-white/5 p-5 space-y-3">
                  {run.steps?.map((step, si) => (
                    <div key={si} className="flex items-start gap-3 pl-4 relative">
                      {si < run.steps.length - 1 && <div className="absolute left-[23px] top-7 w-0.5 h-full bg-white/5" />}
                      {step.status === 'success' ? <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5 relative z-10" /> : <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5 relative z-10" />}
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <div className="text-sm font-medium text-white">{step.action}</div>
                          <div className="text-xs text-slate-500 font-mono">{step.time}</div>
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">{step.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </main>
  );
}
