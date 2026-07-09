import React, { useEffect, useState, useMemo } from 'react';
import api from '../lib/api';
import axios from 'axios';
import { Calendar, AlertTriangle, CheckCircle2, XCircle, Clock, Plus, Trash2, Shield } from 'lucide-react';

const KNOWN_BLACKOUTS = [
  { name: 'Black Friday', date: '2026-11-27', type: 'Retail', risk: 'critical' },
  { name: 'Cyber Monday', date: '2026-11-30', type: 'Retail', risk: 'critical' },
  { name: 'Christmas Eve', date: '2026-12-24', type: 'All', risk: 'high' },
  { name: 'New Year Eve', date: '2026-12-31', type: 'All', risk: 'high' },
  { name: 'Financial Year End (Q4)', date: '2026-03-31', type: 'Finance', risk: 'critical' },
  { name: 'Tax Filing Deadline', date: '2026-04-15', type: 'Finance', risk: 'high' },
  { name: 'Quarter Close (Q1)', date: '2026-06-30', type: 'Finance', risk: 'high' },
  { name: 'Quarter Close (Q2)', date: '2026-09-30', type: 'Finance', risk: 'high' },
  { name: 'Quarter Close (Q3)', date: '2026-12-31', type: 'Finance', risk: 'high' },
  { name: 'Diwali Season', date: '2026-10-20', type: 'APAC', risk: 'high' },
  { name: 'Chinese New Year', date: '2027-02-06', type: 'APAC', risk: 'high' },
  { name: 'Valentine\'s Day (E-commerce)', date: '2027-02-14', type: 'Retail', risk: 'medium' },
];

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export default function BlackoutCalendar() {
  const [waves, setWaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [businessType, setBusinessType] = useState('All');
  const [customBlackouts, setCustomBlackouts] = useState([]);
  const [newBlackout, setNewBlackout] = useState({ name: '', date: '' });

  useEffect(() => {
    api.get('/api/waves')
      .then(res => setWaves(res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Simulate wave dates
  const waveDates = useMemo(() => {
    const waveIds = [...new Set(waves.map(w => w.wave_id))].sort();
    const today = new Date();
    return waveIds.map((id, i) => {
      const start = new Date(today);
      start.setDate(start.getDate() + (i * 28) + 14);
      const end = new Date(start);
      end.setDate(end.getDate() + 14);
      const serverCount = waves.filter(w => w.wave_id === id).length;
      return { id, start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10), serverCount };
    });
  }, [waves]);

  const allBlackouts = useMemo(() => {
    const filtered = businessType === 'All' 
      ? KNOWN_BLACKOUTS 
      : KNOWN_BLACKOUTS.filter(b => b.type === 'All' || b.type === businessType);
    return [...filtered, ...customBlackouts];
  }, [businessType, customBlackouts]);

  // Detect conflicts
  const conflicts = useMemo(() => {
    const results = [];
    waveDates.forEach(wave => {
      const wStart = new Date(wave.start);
      const wEnd = new Date(wave.end);
      
      allBlackouts.forEach(blackout => {
        const bDate = new Date(blackout.date);
        // Check if blackout is within ±7 days of wave window
        const bufferStart = new Date(wStart);
        bufferStart.setDate(bufferStart.getDate() - 3);
        const bufferEnd = new Date(wEnd);
        bufferEnd.setDate(bufferEnd.getDate() + 3);
        
        if (bDate >= bufferStart && bDate <= bufferEnd) {
          // Suggest reschedule
          const newStart = new Date(bDate);
          newStart.setDate(newStart.getDate() + 7);
          results.push({
            wave: wave.id,
            waveStart: wave.start,
            waveEnd: wave.end,
            blackout: blackout.name,
            blackoutDate: blackout.date,
            risk: blackout.risk,
            suggestedStart: newStart.toISOString().slice(0, 10),
          });
        }
      });
    });
    return results;
  }, [waveDates, allBlackouts]);

  const addCustomBlackout = () => {
    if (newBlackout.name && newBlackout.date) {
      setCustomBlackouts(prev => [...prev, { ...newBlackout, type: 'Custom', risk: 'high' }]);
      setNewBlackout({ name: '', date: '' });
    }
  };

  if (loading) return <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full"><div className="text-indigo-400 text-xl font-bold animate-pulse">Loading Wave Schedule...</div></main>;

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-400 tracking-tight mb-2">Migration Blackout Calendar</h1>
        <p className="text-slate-400 font-medium">Prevent migration scheduling conflicts with business-critical dates — Black Friday, quarter-end, tax season, and custom blackout windows.</p>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* Config */}
      <div className="flex gap-4 mb-8 flex-wrap">
        <div className="bg-[#131826] rounded-xl p-4 border border-white/[0.05] flex items-center gap-3">
          <label className="text-xs text-slate-400 font-bold">Business Type</label>
          <select value={businessType} onChange={e => setBusinessType(e.target.value)} className="bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white">
            <option>All</option><option>Retail</option><option>Finance</option><option>APAC</option>
          </select>
        </div>
        <div className="bg-[#131826] rounded-xl p-4 border border-white/[0.05] flex items-center gap-3">
          <input type="text" placeholder="Custom blackout name" value={newBlackout.name} onChange={e => setNewBlackout(p => ({ ...p, name: e.target.value }))} className="bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-xs text-white w-40" />
          <input type="date" value={newBlackout.date} onChange={e => setNewBlackout(p => ({ ...p, date: e.target.value }))} className="bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-xs text-white" />
          <button onClick={addCustomBlackout} disabled={!newBlackout.name || !newBlackout.date} className="bg-amber-600 hover:bg-amber-500 disabled:opacity-30 text-white px-3 py-2 rounded-lg text-xs font-bold transition-colors flex items-center gap-1"><Plus className="w-3 h-3" /> Add</button>
        </div>
      </div>

      {/* Conflict Alert */}
      {conflicts.length > 0 ? (
        <div className="bg-red-500/5 rounded-xl p-6 border border-red-500/20 mb-8">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><AlertTriangle className="w-6 h-6 text-red-400" /> {conflicts.length} Scheduling Conflict{conflicts.length > 1 ? 's' : ''} Detected</h3>
          <div className="space-y-3">
            {conflicts.map((c, i) => (
              <div key={i} className="p-4 bg-slate-900/30 rounded-xl border border-red-500/10 flex items-start gap-4">
                <XCircle className={`w-5 h-5 shrink-0 mt-0.5 ${c.risk === 'critical' ? 'text-red-400' : 'text-amber-400'}`} />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-white">{c.wave}</span>
                    <span className="text-xs text-slate-500">({c.waveStart} → {c.waveEnd})</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${c.risk === 'critical' ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'}`}>{c.risk}</span>
                  </div>
                  <div className="text-sm text-slate-300">Conflicts with <strong className="text-amber-300">{c.blackout}</strong> ({c.blackoutDate})</div>
                  <div className="text-xs text-slate-500 mt-1">💡 Suggested reschedule: Start on <strong className="text-emerald-400">{c.suggestedStart}</strong> (after blackout + buffer)</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-emerald-500/5 rounded-xl p-6 border border-emerald-500/20 mb-8 flex items-center gap-4">
          <CheckCircle2 className="w-8 h-8 text-emerald-400" />
          <div>
            <div className="text-lg font-bold text-emerald-400">✅ No Scheduling Conflicts</div>
            <div className="text-sm text-slate-400">All {waveDates.length} wave windows are clear of known blackout dates.</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Wave Schedule */}
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Calendar className="w-5 h-5 text-indigo-400" /> Wave Schedule</h3>
          <div className="space-y-3">
            {waveDates.map((w, i) => {
              const hasConflict = conflicts.some(c => c.wave === w.id);
              return (
                <div key={i} className={`p-4 rounded-xl border ${hasConflict ? 'bg-red-500/5 border-red-500/20' : 'bg-slate-900/30 border-white/5'}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-white">{w.id}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${hasConflict ? 'bg-red-500/10 text-red-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                      {hasConflict ? '⚠️ Conflict' : '✅ Clear'}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400">{w.start} → {w.end} • {w.serverCount} servers</div>
                </div>
              );
            })}
            {waveDates.length === 0 && <div className="text-sm text-slate-500 text-center p-4">No waves planned yet.</div>}
          </div>
        </div>

        {/* Blackout Dates */}
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Shield className="w-5 h-5 text-amber-400" /> Blackout Dates ({allBlackouts.length})</h3>
          <div className="space-y-2 max-h-[400px] overflow-y-auto custom-scrollbar">
            {allBlackouts.sort((a, b) => a.date.localeCompare(b.date)).map((b, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-slate-900/30 rounded-lg border border-white/5">
                <div className={`w-2 h-2 rounded-full ${b.risk === 'critical' ? 'bg-red-400' : b.risk === 'high' ? 'bg-amber-400' : 'bg-yellow-400'}`} />
                <div className="flex-1">
                  <div className="text-sm font-medium text-white">{b.name}</div>
                  <div className="text-xs text-slate-500">{b.date} • {b.type}</div>
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${b.risk === 'critical' ? 'bg-red-500/10 text-red-400' : b.risk === 'high' ? 'bg-amber-500/10 text-amber-400' : 'bg-yellow-500/10 text-yellow-400'}`}>{b.risk}</span>
                {b.type === 'Custom' && (
                  <button onClick={() => setCustomBlackouts(prev => prev.filter((_, j) => j !== i - KNOWN_BLACKOUTS.filter(kb => businessType === 'All' || kb.type === 'All' || kb.type === businessType).length))} className="p-1 text-slate-500 hover:text-red-400 transition-colors"><Trash2 className="w-3 h-3" /></button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
