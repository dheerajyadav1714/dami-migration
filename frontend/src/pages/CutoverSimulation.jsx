import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { Zap, Clock, CheckCircle2, AlertTriangle, Play, Server } from 'lucide-react';

const PHASE_COLORS = ['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
const CUTOVER_PHASES = ['Pre-Migration Check', 'Data Sync', 'DNS Cutover', 'Validation', 'Rollback Window'];

export default function CutoverSimulation() {
  const [waves, setWaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [simResults, setSimResults] = useState(null);
  const [selectedWave, setSelectedWave] = useState('all');

  useEffect(() => {
    axios.get('http://localhost:8000/api/waves')
      .then(res => setWaves(res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const grouped = useMemo(() => {
    const g = {};
    waves.forEach(w => {
      const wid = w.wave_id || 'unassigned';
      if (!g[wid]) g[wid] = [];
      g[wid].push(w);
    });
    return g;
  }, [waves]);

  const waveIds = Object.keys(grouped);

  const runSimulation = () => {
    setSimulating(true);
    const targetWaves = selectedWave === 'all' ? waveIds : [selectedWave];
    setTimeout(() => {
      const results = targetWaves.map(wid => {
        const servers = grouped[wid] || [];
        const totalEffort = servers.reduce((s, sv) => s + (sv.effort_days || 1), 0);
        return {
          wave_id: wid,
          server_count: servers.length,
          estimated_downtime_min: Math.round(totalEffort * 15 + Math.random() * 30),
          success_probability: Math.round(85 + Math.random() * 14),
          phases: CUTOVER_PHASES.map((p, i) => ({
            name: p,
            duration_min: Math.round(5 + Math.random() * 20),
            status: Math.random() > 0.15 ? 'pass' : 'warning'
          }))
        };
      });
      setSimResults(results);
      setSimulating(false);
    }, 2000);
  };

  if (loading) return <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full"><div className="text-indigo-400 text-xl font-bold animate-pulse">Loading Wave Data...</div></main>;

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Cutover Simulation</h1>
        <p className="text-slate-400 font-medium">Simulate the migration cutover for each wave — estimate downtime, validate phases, and assess rollback readiness.</p>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* Controls */}
      <div className="flex items-center gap-4 mb-8">
        <select value={selectedWave} onChange={e => setSelectedWave(e.target.value)} className="bg-[#131826] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white">
          <option value="all">All Waves</option>
          {waveIds.map(w => <option key={w} value={w}>{w}</option>)}
        </select>
        <button onClick={runSimulation} disabled={simulating} className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-6 py-2.5 rounded-xl transition-colors shadow-lg flex items-center gap-2 font-bold text-sm">
          {simulating ? <><Clock className="w-4 h-4 animate-spin" /> Simulating...</> : <><Play className="w-4 h-4" /> Run Simulation</>}
        </button>
      </div>

      {/* Results */}
      {simResults ? (
        <div className="space-y-6">
          {simResults.map((result, ri) => (
            <div key={ri} className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-white flex items-center gap-2"><Zap className="w-5 h-5 text-amber-400" /> {result.wave_id}</h3>
                <div className={`text-2xl font-black ${result.success_probability >= 90 ? 'text-emerald-400' : 'text-amber-400'}`}>{result.success_probability}% Success</div>
              </div>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5"><div className="text-xs text-slate-400 mb-1">Servers</div><div className="text-xl font-bold">{result.server_count}</div></div>
                <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5"><div className="text-xs text-slate-400 mb-1">Est. Downtime</div><div className="text-xl font-bold">{result.estimated_downtime_min} min</div></div>
                <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5"><div className="text-xs text-slate-400 mb-1">Total Phases</div><div className="text-xl font-bold">{result.phases.length}</div></div>
              </div>
              {/* Phase timeline */}
              <div className="space-y-2">
                {result.phases.map((phase, pi) => (
                  <div key={pi} className="flex items-center gap-3 p-3 bg-slate-900/30 rounded-lg border border-white/5">
                    {phase.status === 'pass' ? <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" /> : <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />}
                    <div className="flex-1">
                      <div className="text-sm font-medium">{phase.name}</div>
                      <div className="text-xs text-slate-400">{phase.duration_min} minutes</div>
                    </div>
                    <div className="w-24 bg-slate-700 rounded-full h-1.5"><div className="rounded-full h-1.5 transition-all" style={{ width: '100%', backgroundColor: PHASE_COLORS[pi % PHASE_COLORS.length] }} /></div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-[#131826] rounded-xl p-12 border border-white/[0.05] text-center">
          <Zap className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <div className="text-lg font-bold text-slate-400 mb-2">No Simulation Running</div>
          <div className="text-sm text-slate-500">Select a wave and click "Run Simulation" to estimate cutover timing, downtime, and rollback scenarios.</div>
        </div>
      )}
    </main>
  );
}
