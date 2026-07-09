import React, { useEffect, useState, useMemo } from 'react';
import api from '../lib/api';
import axios from 'axios';
import { Shield, CheckCircle2, XCircle, AlertTriangle, Cpu, HardDrive, Network, Cloud, RefreshCw } from 'lucide-react';

const DEFAULT_QUOTAS = {
  vcpus: { name: 'vCPUs', limit: 2400, icon: Cpu, unit: '' },
  ssd_gb: { name: 'SSD Persistent Disk', limit: 204800, icon: HardDrive, unit: 'GB' },
  static_ips: { name: 'Static External IPs', limit: 100, icon: Network, unit: '' },
  instances: { name: 'VM Instances', limit: 5000, icon: Cloud, unit: '' },
};

export default function QuotaPreChecker() {
  const [waves, setWaves] = useState([]);
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedWave, setSelectedWave] = useState('all');
  const [customQuotas, setCustomQuotas] = useState(DEFAULT_QUOTAS);

  useEffect(() => {
    Promise.all([
      api.get('/api/waves').catch(() => ({ data: [] })),
      api.get('/api/inventory/servers').catch(() => ({ data: [] })),
    ]).then(([wRes, sRes]) => {
      setWaves(wRes.data || []);
      setServers(sRes.data || []);
    }).finally(() => setLoading(false));
  }, []);

  const waveIds = useMemo(() => {
    const ids = new Set(waves.map(w => w.wave_id));
    return ['all', ...Array.from(ids).sort()];
  }, [waves]);

  const quotaAnalysis = useMemo(() => {
    // Get servers for selected wave
    let waveServers;
    if (selectedWave === 'all') {
      waveServers = servers;
    } else {
      const waveServerNames = new Set(waves.filter(w => w.wave_id === selectedWave).map(w => w.server_name));
      waveServers = servers.filter(s => waveServerNames.has(s.name));
    }

    const required = {
      vcpus: waveServers.reduce((s, sv) => s + (sv.vcpu || 4), 0),
      ssd_gb: waveServers.reduce((s, sv) => s + (sv.disk_gb || 100), 0),
      static_ips: Math.ceil(waveServers.filter(s => s.environment === 'production').length * 0.3),
      instances: waveServers.length,
    };

    return Object.entries(customQuotas).map(([key, quota]) => {
      const need = required[key] || 0;
      const available = quota.limit;
      const usage = available > 0 ? (need / available) * 100 : 0;
      let status = 'ok';
      if (usage > 100) status = 'blocked';
      else if (usage > 80) status = 'warning';

      return { key, ...quota, needed: need, available, usage: Math.min(usage, 100), status, overflow: Math.max(0, need - available) };
    });
  }, [servers, waves, selectedWave, customQuotas]);

  const overallStatus = useMemo(() => {
    if (quotaAnalysis.some(q => q.status === 'blocked')) return 'blocked';
    if (quotaAnalysis.some(q => q.status === 'warning')) return 'warning';
    return 'ok';
  }, [quotaAnalysis]);

  if (loading) return <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full"><div className="text-indigo-400 text-xl font-bold animate-pulse">Checking GCP Quotas...</div></main>;

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-blue-400 tracking-tight mb-2">GCP Quota Pre-Checker</h1>
        <p className="text-slate-400 font-medium">Prevent migration failures by verifying GCP resource quotas are sufficient before starting each wave.</p>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* Wave Selector */}
      <div className="flex items-center gap-4 mb-8">
        <div className="bg-[#131826] rounded-xl p-4 border border-white/[0.05] flex items-center gap-3">
          <label className="text-xs text-slate-400 font-bold">Check Wave</label>
          <select value={selectedWave} onChange={e => setSelectedWave(e.target.value)} className="bg-slate-900 border border-white/10 rounded-lg px-4 py-2 text-sm text-white">
            {waveIds.map(w => <option key={w} value={w}>{w === 'all' ? 'All Waves (Full Migration)' : w}</option>)}
          </select>
        </div>
      </div>

      {/* Overall Status Banner */}
      <div className={`mb-8 p-6 rounded-xl border flex items-center gap-4 ${
        overallStatus === 'blocked' ? 'bg-red-500/5 border-red-500/20' :
        overallStatus === 'warning' ? 'bg-amber-500/5 border-amber-500/20' :
        'bg-emerald-500/5 border-emerald-500/20'
      }`}>
        {overallStatus === 'blocked' ? <XCircle className="w-10 h-10 text-red-400" /> :
         overallStatus === 'warning' ? <AlertTriangle className="w-10 h-10 text-amber-400" /> :
         <CheckCircle2 className="w-10 h-10 text-emerald-400" />}
        <div>
          <div className="text-2xl font-bold text-white">
            {overallStatus === 'blocked' ? '🔴 BLOCKED — Quota Exceeded' :
             overallStatus === 'warning' ? '🟡 WARNING — Near Quota Limits' :
             '🟢 GO — All Quotas Sufficient'}
          </div>
          <div className="text-sm text-slate-400 mt-1">
            {overallStatus === 'blocked' ? 'Request quota increases before starting this wave. Estimated approval: 2-3 business days.' :
             overallStatus === 'warning' ? 'Some resources are near limits. Consider requesting increases proactively.' :
             `All resource quotas are sufficient for ${selectedWave === 'all' ? 'full migration' : selectedWave}.`}
          </div>
        </div>
      </div>

      {/* Quota Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {quotaAnalysis.map((q) => {
          const IconComp = q.icon;
          return (
            <div key={q.key} className={`bg-[#131826] rounded-xl p-6 border ${q.status === 'blocked' ? 'border-red-500/30' : q.status === 'warning' ? 'border-amber-500/20' : 'border-white/[0.05]'}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${q.status === 'blocked' ? 'bg-red-600/20 border border-red-500/30' : q.status === 'warning' ? 'bg-amber-600/20 border border-amber-500/30' : 'bg-slate-800 border border-white/10'}`}>
                    <IconComp className={`w-5 h-5 ${q.status === 'blocked' ? 'text-red-400' : q.status === 'warning' ? 'text-amber-400' : 'text-slate-300'}`} />
                  </div>
                  <div>
                    <div className="font-bold text-white">{q.name}</div>
                    <div className="text-xs text-slate-500">Region: us-central1</div>
                  </div>
                </div>
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                  q.status === 'blocked' ? 'bg-red-500/10 text-red-400' :
                  q.status === 'warning' ? 'bg-amber-500/10 text-amber-400' :
                  'bg-emerald-500/10 text-emerald-400'
                }`}>
                  {q.status === 'blocked' ? '🔴 BLOCKED' : q.status === 'warning' ? '🟡 WARNING' : '✅ OK'}
                </span>
              </div>

              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-slate-400">Need: <strong className="text-white">{q.needed.toLocaleString()}{q.unit && ` ${q.unit}`}</strong></span>
                <span className="text-slate-400">Limit: <strong className="text-white">{q.available.toLocaleString()}{q.unit && ` ${q.unit}`}</strong></span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-700 rounded-full h-3 mb-2">
                <div className={`h-3 rounded-full transition-all ${q.status === 'blocked' ? 'bg-red-500' : q.status === 'warning' ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${Math.min(q.usage, 100)}%` }} />
              </div>
              <div className="text-xs text-slate-500">{q.usage.toFixed(1)}% utilized{q.overflow > 0 ? ` — needs ${q.overflow.toLocaleString()} more` : ''}</div>

              {/* Editable Quota */}
              <div className="mt-3 flex items-center gap-2">
                <label className="text-[10px] text-slate-500 font-bold">Custom limit:</label>
                <input
                  type="number"
                  value={customQuotas[q.key].limit}
                  onChange={e => setCustomQuotas(prev => ({ ...prev, [q.key]: { ...prev[q.key], limit: parseInt(e.target.value) || 0 } }))}
                  className="bg-slate-900 border border-white/10 rounded px-2 py-1 text-xs text-white w-24"
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Actions */}
      {overallStatus === 'blocked' && (
        <div className="bg-red-500/5 rounded-xl p-6 border border-red-500/20">
          <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-red-400" /> Required Actions</h3>
          <div className="space-y-2">
            {quotaAnalysis.filter(q => q.status === 'blocked').map(q => (
              <div key={q.key} className="flex items-center gap-3 p-3 bg-slate-900/30 rounded-lg border border-red-500/10">
                <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                <span className="text-sm text-slate-300">Request quota increase for <strong className="text-white">{q.name}</strong>: need {q.needed.toLocaleString()}, have {q.available.toLocaleString()} (deficit: {q.overflow.toLocaleString()})</span>
              </div>
            ))}
            <p className="text-xs text-slate-500 mt-2">GCP quota increase requests typically take 2-3 business days. Submit via <a href="https://console.cloud.google.com/iam-admin/quotas" target="_blank" rel="noopener" className="text-indigo-400 hover:underline">GCP Console → IAM → Quotas</a></p>
          </div>
        </div>
      )}
    </main>
  );
}
