import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import axios from 'axios';
import { 
  Download, 
  Server, 
  Layers, 
  DollarSign, 
  ShieldCheck, 
  CheckCircle2,
  Zap,
  Network, 
  Waves, 
  Building2, 
  Code2, 
  Rocket, 
  Calendar,
  BookOpen,
  Search,
  Link as LinkIcon
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

export default function ExecutiveDashboard() {
  const [stats, setStats] = useState({
    total_servers: 0,
    total_apps: 0,
    total_dbs: 0,
    total_waves: 0,
    savings_val: 0,
    savings_pct: 0,
    name: 'Loading...',
    client_name: 'Loading...',
    phase: 'Discovery'
  });
  
  const [readiness, setReadiness] = useState({
    overall_score: 0,
    dimension_scores: { "Discovery": 0, "Risk Assessment": 0, "Wave Planning": 0, "Architecture": 0, "Compliance": 0 }
  });

  const [benchmarks, setBenchmarks] = useState({
    has_real_benchmarks: false,
    real_benchmarks: [],
    simulated_benchmarks: []
  });

  const [velocity, setVelocity] = useState([]);
  const [activities, setActivities] = useState([]);

  const [timeRange, setTimeRange] = useState('1M');

  const [loading, setLoading] = useState(true);
  const [orchestratorPrompt, setOrchestratorPrompt] = useState('');
  const [orchestratorLoading, setOrchestratorLoading] = useState(false);
  const [orchestratorResponse, setOrchestratorResponse] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, readinessRes, benchRes, velRes, actRes] = await Promise.all([
          api.get('/api/project/stats').catch(() => ({data: {}})),
          api.get('/api/project/readiness').catch(() => ({data: {overall_score: 0, dimension_scores: {}}})),
          api.get('/api/project/benchmarks').catch(() => ({data: {has_real_benchmarks: false, real_benchmarks: [], simulated_benchmarks: []}})),
          api.get('/api/charts/migration-velocity').catch(() => ({data: []})),
          api.get('/api/project/activity').catch(() => ({data: []}))
        ]);
        
        if (statsRes.data.total_servers !== undefined) setStats(statsRes.data);
        if (readinessRes.data.overall_score !== undefined) setReadiness(readinessRes.data);
        if (benchRes.data.simulated_benchmarks !== undefined) setBenchmarks(benchRes.data);
        if (velRes.data.length > 0) setVelocity(velRes.data);
        if (actRes.data.length > 0) setActivities(actRes.data);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  const handleOrchestratorRun = async (e) => {
    e.preventDefault();
    if (!orchestratorPrompt.trim()) return;
    
    setOrchestratorLoading(true);
    setOrchestratorResponse(null);
    try {
      const res = await api.post('/api/run-orchestrator', { prompt: orchestratorPrompt });
      setOrchestratorResponse({ success: true, text: res.data.final_response || "Command executed successfully.", tools: res.data.triggered_tools || [] });
    } catch (err) {
      setOrchestratorResponse({ success: false, text: "Orchestrator unavailable or failed to execute." });
    } finally {
      setOrchestratorLoading(false);
    }
  };

  const runAgent = async (phase) => {
    try {
      await api.post('/api/run-agent', { project_id: 'proj-migration-001', phase });
      alert(`Triggered ${phase} agent successfully!`);
    } catch(e) {
      alert(`Failed to trigger ${phase} agent.`);
    }
  };

  if (loading) {
    return (
      <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full">
        <div className="text-indigo-400 text-xl font-bold animate-pulse">Initializing Mission Control...</div>
      </main>
    );
  }

  const currentProgressPct = 67; // Hardcoded for demo

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar">
        {/* PREMIUM HEADER */}
        <header className="flex justify-between items-start mb-8">
            <div>
                <h2 className="text-4xl font-extrabold mb-1">Executive Dashboard</h2>
                <p className="text-slate-400 text-sm font-medium flex items-center gap-2">
                    Project: <strong className="text-white">{stats.name}</strong> <span className="text-slate-600">|</span> Client: <strong className="text-white">{stats.client_name}</strong>
                </p>
            </div>
            <div className="flex gap-3">
                <button 
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-lg font-semibold transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)] flex items-center gap-2 text-sm"
                  onClick={async () => {
                    try {
                      const res = await api.post('/api/chat', { prompt: `Generate a comprehensive executive migration report for project "${stats.name}" for client "${stats.client_name}". Include: ${stats.total_servers} servers discovered, ${stats.total_waves} migration waves planned, estimated annual savings of $${stats.savings_val}, current phase: ${stats.phase}. Format as a professional executive summary with sections for Overview, Key Metrics, Risk Assessment, Wave Plan Summary, Cost Analysis, and Next Steps.` });
                      const report = res.data?.reply || 'Report generation failed.';
                      const blob = new Blob([report], {type: 'text/markdown'});
                      const a = document.createElement('a');
                      a.href = URL.createObjectURL(blob);
                      a.download = `DAMI_Executive_Report_${new Date().toISOString().slice(0,10)}.md`;
                      a.click();
                    } catch {
                      alert('Failed to generate report. Ensure backend is running.');
                    }
                  }}
                >
                    <Rocket className="w-4 h-4" /> Generate Report
                </button>
                <button 
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-lg font-semibold transition-all shadow-[0_0_15px_rgba(79,70,229,0.4)] flex items-center gap-2 text-sm"
                  onClick={() => {
                    const report = `# D.A.M.I. Executive Migration Report\n## Project: ${stats.name}\n## Client: ${stats.client_name}\n## Generated: ${new Date().toLocaleString()}\n\n---\n\n### Key Metrics\n| Metric | Value |\n|--------|-------|\n| Total Servers Discovered | ${stats.total_servers} VMs |\n| Migration Waves Planned | ${stats.total_waves} |\n| Estimated Annual Savings | $${(stats.savings_val / 1000).toFixed(0)}K (${stats.savings_pct}%) |\n| Current Phase | ${stats.phase} |\n| Migration Readiness | ${readiness.overall_score}% |\n\n### Readiness Dimensions\n${Object.entries(readiness.dimension_scores).map(([k, v]) => `- **${k}**: ${v}%`).join('\n')}\n\n### NVIDIA RAPIDS Acceleration\n${(benchmarks.has_real_benchmarks ? benchmarks.real_benchmarks : benchmarks.simulated_benchmarks).map(b => `- ${b.rows_processed} rows: CPU ${b.pandas_cpu_ms || b.processing_seconds}ms → GPU ${b.cudf_gpu_ms || '-'}ms (${b.speedup || b.speedup_factor + 'x'})`).join('\n')}\n`;
                    const blob = new Blob([report], {type: 'text/markdown'});
                    const a = document.createElement('a');
                    a.href = URL.createObjectURL(blob);
                    a.download = `DAMI_Executive_Report_${new Date().toISOString().slice(0,10)}.md`;
                    a.click();
                  }}
                >
                    <Download className="w-4 h-4" /> Export Report
                </button>
            </div>
        </header>

        {/* PREMIUM KPI CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {/* Servers */}
            <div className="bg-[#131826] rounded-2xl p-6 relative overflow-hidden border border-white/[0.05] shadow-lg group">
                <Server className="absolute -right-4 -bottom-4 w-32 h-32 text-white/[0.02] group-hover:text-white/[0.04] transition-colors" />
                <div className="flex justify-between items-start mb-4 relative z-10">
                    <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                        <Server className="w-5 h-5 text-slate-300" />
                    </div>
                    <span className="inline-flex px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/20">
                        ↗ 100% VMware
                    </span>
                </div>
                <h3 className="text-4xl font-bold text-white mb-1 relative z-10">{stats.total_servers}</h3>
                <p className="text-slate-400 text-xs font-bold tracking-wider uppercase relative z-10">Total Servers</p>
            </div>
            
            {/* Waves */}
            <div className="bg-[#131826] rounded-2xl p-6 relative overflow-hidden border border-white/[0.05] shadow-lg group">
                <Layers className="absolute -right-4 -bottom-4 w-32 h-32 text-white/[0.02] group-hover:text-white/[0.04] transition-colors" />
                <div className="flex justify-between items-start mb-4 relative z-10">
                    <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                        <Layers className="w-5 h-5 text-slate-300" />
                    </div>
                </div>
                <h3 className="text-4xl font-bold text-white mb-1 relative z-10">{stats.total_waves}</h3>
                <p className="text-slate-400 text-xs font-bold tracking-wider uppercase relative z-10">Migration Waves</p>
            </div>

            {/* Savings */}
            <div className="bg-[#131826] rounded-2xl p-6 relative overflow-hidden border border-white/[0.05] shadow-lg group">
                <DollarSign className="absolute -right-4 -bottom-4 w-32 h-32 text-white/[0.02] group-hover:text-white/[0.04] transition-colors" />
                <div className="flex justify-between items-start mb-4 relative z-10">
                    <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                        <DollarSign className="w-5 h-5 text-emerald-400" />
                    </div>
                    <span className="inline-flex px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/20">
                        ↘ {stats.savings_pct}%
                    </span>
                </div>
                <h3 className="text-4xl font-bold text-white mb-1 relative z-10">${(stats.savings_val / 1000).toFixed(0)}k</h3>
                <p className="text-slate-400 text-xs font-bold tracking-wider uppercase relative z-10">Est. Annual Savings</p>
            </div>

            {/* Compliance */}
            <div className="bg-[#131826] rounded-2xl p-6 relative overflow-hidden border border-white/[0.05] shadow-lg group">
                <ShieldCheck className="absolute -right-4 -bottom-4 w-32 h-32 text-white/[0.02] group-hover:text-white/[0.04] transition-colors" />
                <div className="flex justify-between items-start mb-4 relative z-10">
                    <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                        <ShieldCheck className="w-5 h-5 text-slate-300" />
                    </div>
                </div>
                <h3 className="text-4xl font-bold text-white mb-1 relative z-10">Zero</h3>
                <p className="text-slate-400 text-xs font-bold tracking-wider uppercase relative z-10">Compliance Risks</p>
            </div>
        </div>

        {/* VELOCITY & ACTIVITY ROW */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Migration Velocity Chart */}
            <div className="lg:col-span-2 bg-[#131826] rounded-2xl p-6 border border-white/[0.05] shadow-lg">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-bold text-white">Migration Velocity</h3>
                    <div className="flex bg-slate-900 rounded-lg p-1">
                        <button 
                          className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${timeRange === '1W' ? 'bg-white/10 text-white shadow' : 'text-slate-400 hover:text-white'}`}
                          onClick={() => setTimeRange('1W')}
                        >1W</button>
                        <button 
                          className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${timeRange === '1M' ? 'bg-white/10 text-white shadow' : 'text-slate-400 hover:text-white'}`}
                          onClick={() => setTimeRange('1M')}
                        >1M</button>
                        <button 
                          className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${timeRange === '1Y' ? 'bg-white/10 text-white shadow' : 'text-slate-400 hover:text-white'}`}
                          onClick={() => setTimeRange('1Y')}
                        >1Y</button>
                    </div>
                </div>
                <div className="h-[250px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={velocity} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorMigrated" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
                            <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                            <Tooltip 
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff', borderRadius: '8px' }}
                                itemStyle={{ color: '#818cf8' }}
                            />
                            <Area type="monotone" dataKey="migrated" stroke="#818cf8" strokeWidth={3} fillOpacity={1} fill="url(#colorMigrated)" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Activity Feed */}
            <div className="lg:col-span-1 bg-[#131826] rounded-2xl p-6 border border-white/[0.05] shadow-lg">
                <h3 className="text-lg font-bold text-white mb-6">Activity</h3>
                <div className="space-y-6">
                    {activities.map((act) => {
                        let icon = <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
                        let bg = "bg-emerald-500/10";
                        if (act.type === 'terraform') {
                            icon = <Code2 className="w-4 h-4 text-slate-300" />;
                            bg = "bg-slate-700/50";
                        } else if (act.type === 'system') {
                            icon = <Zap className="w-4 h-4 text-slate-300" />;
                            bg = "bg-slate-700/50";
                        }
                        
                        return (
                            <div key={act.id} className="flex gap-4">
                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${bg}`}>
                                    {icon}
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-slate-200">{act.action}</p>
                                    <p className="text-xs text-slate-500">{act.time}</p>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>

        {/* ACCELERATION & READINESS */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-[#131826] rounded-2xl p-6 border border-white/[0.05] shadow-lg">
                <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2"><Zap className="text-orange-400 w-5 h-5" /> Acceleration Impact</h3>
                <div className="space-y-4">
                    <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4 flex justify-between items-center">
                        <div>
                            <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1">Traditional Method</div>
                            <div className="text-sm text-slate-300 font-medium">Manual tracking, external consultants</div>
                        </div>
                        <div className="text-xl font-bold text-red-400">6-18 mos</div>
                    </div>
                    <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4 flex justify-between items-center">
                        <div>
                            <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1">D.A.M.I. AI Pipeline</div>
                            <div className="text-sm text-slate-300 font-medium">AI Agents + BQML + cuDF</div>
                        </div>
                        <div className="text-xl font-bold text-emerald-400">~8 mins</div>
                    </div>
                    <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-4 flex justify-between items-center">
                        <div>
                            <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1">Total Acceleration</div>
                            <div className="text-sm text-slate-300 font-medium">Faster time-to-decision</div>
                        </div>
                        <div className="text-2xl font-black text-indigo-400">500x+</div>
                    </div>
                </div>
            </div>

            <div className="bg-[#131826] rounded-2xl p-6 border border-white/[0.05] shadow-lg flex flex-col justify-center">
                <h3 className="text-lg font-bold text-white mb-6">Migration Readiness Dimensions</h3>
                <div className="space-y-5">
                  {Object.entries(readiness.dimension_scores).map(([dim, score]) => {
                    let color = "#10b981"; // emerald
                    if (score < 40) color = "#ef4444"; // red
                    else if (score < 60) color = "#f59e0b"; // amber
                    else if (score < 80) color = "#6366f1"; // indigo
                    
                    return (
                      <div key={dim}>
                          <div className="flex justify-between text-xs font-bold mb-1.5">
                              <span className="text-slate-300">{dim}</span>
                              <span style={{ color }}>{score}%</span>
                          </div>
                          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                              <div 
                                className="h-full rounded-full transition-all duration-1000" 
                                style={{ width: `${score}%`, backgroundColor: color }}
                              />
                          </div>
                      </div>
                    );
                  })}
                </div>
            </div>
        </div>

        {/* ORCHESTRATOR & PROGRESS TIMELINE */}
        <div className="bg-[#131826] rounded-2xl p-6 border border-white/[0.05] shadow-lg mb-8">
            <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2"><Calendar className="w-5 h-5 text-indigo-400" /> Migration Progress Timeline</h3>
            
            <div className="flex justify-between items-center mb-2">
                <span className="font-semibold text-slate-400 text-xs">OVERALL PROGRESS</span>
                <span className="font-bold text-indigo-400 text-sm">67% — 5/9 phases complete</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mb-8">
                <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: '67%' }}></div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-9 gap-4 mb-8">
                {[
                  { name: "Discovery", icon: Search, status: "Done" },
                  { name: "Risk Assess", icon: ShieldCheck, status: "Done" },
                  { name: "Dependencies", icon: Network, status: "Done" },
                  { name: "Wave Plan", icon: Waves, status: "Done" },
                  { name: "Architecture", icon: Building2, status: "Done" },
                  { name: "IaC Gen", icon: Code2, status: "Running" },
                  { name: "Compliance", icon: ShieldCheck, status: "Running" },
                  { name: "Execution", icon: Rocket, status: "Pending" },
                  { name: "Validation", icon: CheckCircle2, status: "Pending" }
                ].map((p, i) => {
                  let bg = "bg-slate-800/20";
                  let iconColor = "text-slate-600";
                  let border = "border-transparent";

                  if (p.status === "Done") {
                    bg = "bg-emerald-500/10";
                    iconColor = "text-emerald-500";
                    border = "border-emerald-500/20";
                  } else if (p.status === "Running") {
                    bg = "bg-indigo-500/10";
                    iconColor = "text-indigo-400";
                    border = "border-indigo-500/30";
                  }

                  const Icon = p.icon;
                  return (
                    <div key={i} className={`flex flex-col items-center justify-center p-4 rounded-xl border ${bg} ${border} text-center`}>
                        <Icon className={`w-5 h-5 mb-2 ${iconColor}`} />
                        <div className="text-[10px] font-bold text-slate-300 leading-tight h-6 flex items-center justify-center">{p.name}</div>
                    </div>
                  );
                })}
            </div>

            <div className="border-t border-white/[0.05] pt-6 flex flex-col md:flex-row gap-6">
                <div className="flex-1">
                    <h4 className="text-sm font-bold text-white mb-2 flex items-center gap-2">💬 Orchestrator Chat</h4>
                    <p className="text-xs text-slate-400 mb-3">Ask D.A.M.I. to run phases autonomously:</p>
                    <form onSubmit={handleOrchestratorRun} className="flex gap-2">
                        <input 
                          type="text" 
                          value={orchestratorPrompt}
                          onChange={e => setOrchestratorPrompt(e.target.value)}
                          placeholder="e.g., Run dependency mapper..."
                          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
                        />
                        <button type="submit" disabled={orchestratorLoading} className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2">
                            {orchestratorLoading ? "⚙️" : "Send"}
                        </button>
                    </form>
                    {orchestratorResponse && (
                      <div className={`mt-3 p-3 rounded-lg text-xs ${orchestratorResponse.success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                        {orchestratorResponse.text}
                      </div>
                    )}
                </div>
                
                <div className="flex-1 flex gap-2 items-end">
                    <button onClick={() => runAgent("discovery")} className="flex-1 bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-300 py-2.5 rounded-lg transition-colors">Run Discovery</button>
                    <button onClick={() => runAgent("risk")} className="flex-1 bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-300 py-2.5 rounded-lg transition-colors">Run Risk</button>
                    <button onClick={() => runAgent("wave")} className="flex-1 bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-300 py-2.5 rounded-lg transition-colors">Run Waves</button>
                </div>
            </div>
        </div>

        {/* GPU BENCHMARKS */}
        <div className="bg-[#131826] rounded-2xl p-6 border border-white/[0.05] shadow-lg mb-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-white flex items-center gap-2"><Zap className="text-emerald-400 w-5 h-5" /> NVIDIA RAPIDS Performance Metrics</h3>
              <div className="flex items-center gap-3">
                <button 
                  onClick={() => { api.get('/api/project/benchmarks').then(r => setBenchmarks(r.data)).catch(()=>{}); }}
                  className="text-xs px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-600/40 transition-all font-semibold"
                >
                  ↻ Refresh Results
                </button>
                <a 
                  href="https://colab.research.google.com/github/dheerajyadav1714/dami-migration/blob/refinement-v3/notebooks/rapids_live_benchmark.ipynb"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs px-3 py-1.5 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-600/40 transition-all font-semibold flex items-center gap-1.5"
                >
                  <Rocket className="w-3.5 h-3.5" /> Open in Colab
                </a>
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-1">
                    <div className="mb-4">
                        {benchmarks.has_real_benchmarks ? (
                          <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-3 py-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                              <span className="text-emerald-500 font-bold text-[10px] uppercase tracking-wider">Live Results</span>
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-full px-3 py-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                              <span className="text-amber-500 font-bold text-[10px] uppercase tracking-wider">Simulated Results</span>
                          </div>
                        )}
                    </div>
                    <table className="w-full text-xs text-left mb-6">
                        <thead className="text-slate-400 border-b border-white/5">
                            <tr>
                                <th className="py-2 font-semibold">Rows</th>
                                <th className="py-2 font-semibold text-right">CPU</th>
                                <th className="py-2 font-semibold text-right">GPU</th>
                                <th className="py-2 font-semibold text-right">Gain</th>
                            </tr>
                        </thead>
                        <tbody className="text-slate-300 divide-y divide-white/5">
                            {(benchmarks.has_real_benchmarks ? benchmarks.real_benchmarks : benchmarks.simulated_benchmarks).map((row, i) => (
                                <tr key={i}>
                                    <td className="py-2">{row.rows_processed}</td>
                                    <td className="py-2 text-right">{row.pandas_cpu_ms || row.processing_seconds}ms</td>
                                    <td className="py-2 text-right text-emerald-400">{row.cudf_gpu_ms || '-'}ms</td>
                                    <td className="py-2 text-right font-bold text-indigo-400">{row.speedup || row.speedup_factor + 'x'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                
                <div className="lg:col-span-2 h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={benchmarks.has_real_benchmarks ? benchmarks.real_benchmarks : benchmarks.simulated_benchmarks} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="rows_processed" stroke="#64748b" tick={{fontSize: 10}} tickFormatter={v => `${v/1000}k`} axisLine={false} tickLine={false} />
                            <YAxis stroke="#64748b" tick={{fontSize: 10}} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff'}} itemStyle={{fontSize: 12}} />
                            <Legend wrapperStyle={{fontSize: 10, paddingTop: '10px'}} />
                            <Bar dataKey={benchmarks.has_real_benchmarks ? "processing_seconds" : "pandas_cpu_ms"} name="Pandas (CPU)" fill="#334155" barSize={12} radius={[2,2,0,0]} />
                            <Bar dataKey={benchmarks.has_real_benchmarks ? "cudf_gpu_ms" : "cudf_gpu_ms"} name="cuDF (GPU)" fill="#10b981" barSize={12} radius={[2,2,0,0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>

        {/* COLAB LIVE BENCHMARK */}
        <div className="bg-[#131826] rounded-2xl overflow-hidden border border-white/[0.05] shadow-lg mb-8">
            <div className="bg-gradient-to-r from-[#0f141f] to-[#1a1040] px-6 py-4 flex items-center justify-between border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-yellow-500 flex items-center justify-center text-white font-bold text-sm">G</div>
                <div>
                  <div className="text-white font-bold text-sm">Live GPU Benchmark — Google Colab</div>
                  <div className="text-slate-400 text-xs">Run real-time CPU vs GPU comparison on NVIDIA T4</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <a
                  href="https://colab.research.google.com/github/dheerajyadav1714/dami-migration/blob/refinement-v3/notebooks/rapids_live_benchmark.ipynb" 
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 rounded-xl text-sm font-bold bg-gradient-to-r from-emerald-600 to-teal-600 border border-emerald-500/50 hover:from-emerald-500 hover:to-teal-500 text-white transition-all flex items-center gap-2 shadow-lg shadow-emerald-600/20"
                >
                  <Rocket className="w-4 h-4" /> Open in New Tab
                </a>
              </div>
            </div>

            {/* INSTRUCTIONS */}
            <div className="bg-[#0d1117] px-6 py-4 border-b border-white/5">
              <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-3">How to Run the Live Benchmark</div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div className="flex items-start gap-3 bg-white/[0.02] rounded-lg p-3 border border-white/5">
                  <div className="w-7 h-7 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-300 font-bold text-xs shrink-0">1</div>
                  <div>
                    <div className="text-white text-xs font-bold mb-0.5">Select GPU Runtime</div>
                    <div className="text-slate-400 text-[10px] leading-tight">In Colab: Runtime → Change runtime type → <span className="text-emerald-400 font-semibold">T4 GPU</span> → Save</div>
                  </div>
                </div>
                <div className="flex items-start gap-3 bg-white/[0.02] rounded-lg p-3 border border-white/5">
                  <div className="w-7 h-7 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-300 font-bold text-xs shrink-0">2</div>
                  <div>
                    <div className="text-white text-xs font-bold mb-0.5">Run All Cells</div>
                    <div className="text-slate-400 text-[10px] leading-tight">Click <span className="text-emerald-400 font-semibold">Runtime → Run all</span> or press Ctrl+F9. Allow access when prompted.</div>
                  </div>
                </div>
                <div className="flex items-start gap-3 bg-white/[0.02] rounded-lg p-3 border border-white/5">
                  <div className="w-7 h-7 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-300 font-bold text-xs shrink-0">3</div>
                  <div>
                    <div className="text-white text-xs font-bold mb-0.5">Watch the Results</div>
                    <div className="text-slate-400 text-[10px] leading-tight">CPU runs first (slow), then GPU (fast). <span className="text-emerald-400 font-semibold">Charts auto-generate</span> with speedup comparison.</div>
                  </div>
                </div>
                <div className="flex items-start gap-3 bg-white/[0.02] rounded-lg p-3 border border-white/5">
                  <div className="w-7 h-7 rounded-full bg-emerald-600/30 border border-emerald-500/40 flex items-center justify-center text-emerald-300 font-bold text-xs shrink-0">4</div>
                  <div>
                    <div className="text-white text-xs font-bold mb-0.5">See Live Results Here</div>
                    <div className="text-slate-400 text-[10px] leading-tight">Results auto-write to BigQuery. Click <span className="text-emerald-400 font-semibold">↻ Refresh Results</span> above to update the dashboard.</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="w-full h-[600px] bg-black">
              <iframe
                src="https://colab.research.google.com/github/dheerajyadav1714/dami-migration/blob/refinement-v3/notebooks/rapids_live_benchmark.ipynb"
                width="100%"
                height="100%"
                frameBorder="0"
                style={{ border: 0 }}
                allowFullScreen
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope"
              ></iframe>
            </div>
        </div>

        {/* LOOKER STUDIO IFRAME */}
        <div className="mb-10">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
               <BookOpen className="w-5 h-5 text-indigo-400" /> Legacy Report Archive (Looker Studio)
            </h3>
            <div className="bg-[#131826] rounded-2xl overflow-hidden border border-white/[0.05] shadow-lg shrink-0">
                <div className="bg-[#0f141f] px-4 py-3 flex items-center border-b border-white/5">
                    <div className="flex gap-2 mr-4">
                        <div className="w-3 h-3 rounded-full bg-slate-600"></div>
                        <div className="w-3 h-3 rounded-full bg-slate-600"></div>
                        <div className="w-3 h-3 rounded-full bg-slate-600"></div>
                    </div>
                    <div className="flex-1 flex justify-center">
                        <span className="text-xs font-mono text-slate-500">lookerstudio.google.com/reporting/...</span>
                    </div>
                </div>
                <div className="w-full h-[800px] bg-black">
                    <iframe 
                        src="https://datastudio.google.com/embed/reporting/56bf16f7-97ce-45a8-8354-f5bfcffe6d0d/page/EKu2F" 
                        width="100%" 
                        height="100%" 
                        frameBorder="0" 
                        style={{ border: 0 }} 
                        allowFullScreen
                    ></iframe>
                </div>
            </div>
        </div>
    </main>
  );
}
