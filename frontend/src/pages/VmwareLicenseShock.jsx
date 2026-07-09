import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { DollarSign, AlertTriangle, TrendingDown, Clock, Server, Cloud, Download, Loader2 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, AreaChart, Area } from 'recharts';

export default function VmwareLicenseShock() {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [renewalDate, setRenewalDate] = useState('2026-03-01');
  const [coresPerHost, setCoresPerHost] = useState(32);

  useEffect(() => {
    axios.get('http://localhost:8000/api/inventory/servers')
      .then(res => setServers(res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const analysis = useMemo(() => {
    const totalVMs = servers.length;
    const totalVCPUs = servers.reduce((s, sv) => s + (sv.vcpu || 4), 0);
    // Estimate ESXi hosts (assume ~40 VMs per host average)
    const estimatedHosts = Math.max(1, Math.ceil(totalVMs / 40));
    const totalCores = estimatedHosts * coresPerHost;

    // OLD VMware Pricing (pre-Broadcom)
    const oldVSphere = estimatedHosts * 4000;
    const oldVSAN = estimatedHosts * 3500;
    const oldNSX = estimatedHosts * 6500;
    const oldTotal = oldVSphere + oldVSAN + oldNSX;

    // NEW Broadcom Pricing (VCF per-core, 2024+)
    const broadcomPerCore = 180;
    const newTotal = totalCores * broadcomPerCore * 3.5; // Broadcom multiplier
    const priceIncrease = ((newTotal - oldTotal) / oldTotal * 100).toFixed(0);

    // GCP Equivalent (right-sized)
    const gcpMonthly = totalVCPUs * 22; // ~$22/vCPU/month average
    const gcpAnnual = gcpMonthly * 12;
    const gcpWithCUD = Math.round(gcpAnnual * 0.63); // 37% CUD discount

    const savings = newTotal - gcpWithCUD;
    const savingsPct = ((savings / newTotal) * 100).toFixed(1);

    // Break-even
    const migrationCost = totalVMs * 500; // ~$500 per VM migration cost
    const monthlyBreakeven = Math.ceil(migrationCost / (savings / 12));

    // Days until renewal
    const renewal = new Date(renewalDate);
    const today = new Date();
    const daysUntil = Math.max(0, Math.ceil((renewal - today) / (1000 * 60 * 60 * 24)));

    // 3-year projection
    const projection = [
      { year: 'Year 1', vmware: newTotal, gcp: gcpWithCUD + migrationCost, label: 'Migration Year' },
      { year: 'Year 2', vmware: newTotal, gcp: gcpWithCUD, label: 'Steady State' },
      { year: 'Year 3', vmware: Math.round(newTotal * 1.08), gcp: Math.round(gcpWithCUD * 0.95), label: 'Optimized' },
    ];

    const costBreakdown = [
      { name: 'Old VMware', cost: oldTotal, fill: '#6366f1' },
      { name: 'New Broadcom', cost: newTotal, fill: '#ef4444' },
      { name: 'GCP (On-Demand)', cost: gcpAnnual, fill: '#3b82f6' },
      { name: 'GCP (CUD 3yr)', cost: gcpWithCUD, fill: '#10b981' },
    ];

    return {
      totalVMs, totalVCPUs, estimatedHosts, totalCores,
      oldTotal, newTotal, priceIncrease,
      gcpAnnual, gcpWithCUD, savings, savingsPct,
      migrationCost, monthlyBreakeven, daysUntil,
      projection, costBreakdown
    };
  }, [servers, renewalDate, coresPerHost]);

  const fmt = (v) => `$${(v/1000).toFixed(0)}K`;

  const exportReport = () => {
    const r = analysis;
    let report = `# VMware Broadcom License Shock Analysis\n_Generated: ${new Date().toLocaleString()}_\n\n`;
    report += `## Environment\n- VMs: ${r.totalVMs.toLocaleString()}\n- Estimated ESXi Hosts: ${r.estimatedHosts}\n- Total Cores: ${r.totalCores}\n\n`;
    report += `## Cost Comparison (Annual)\n| Scenario | Cost |\n|----------|------|\n| Old VMware (pre-Broadcom) | ${fmt(r.oldTotal)} |\n| New Broadcom VCF | ${fmt(r.newTotal)} (+${r.priceIncrease}%) |\n| GCP Equivalent (On-Demand) | ${fmt(r.gcpAnnual)} |\n| GCP with CUD | ${fmt(r.gcpWithCUD)} |\n\n`;
    report += `## Recommendation\n- **Annual Savings**: ${fmt(r.savings)} (${r.savingsPct}%)\n- **Migration Cost**: ${fmt(r.migrationCost)}\n- **Break-even**: ${r.monthlyBreakeven} months\n- **Days until VMware renewal**: ${r.daysUntil}\n- **Urgency**: ${r.daysUntil < 180 ? '🔴 HIGH' : '🟡 MEDIUM'}\n`;
    const blob = new Blob([report], { type: 'text/markdown' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = `DAMI_VMware_License_Analysis_${new Date().toISOString().slice(0,10)}.md`; a.click();
  };

  if (loading) return <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full"><div className="text-indigo-400 text-xl font-bold animate-pulse">Analyzing VMware Licensing...</div></main>;

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-amber-400 tracking-tight mb-2">VMware License Shock Calculator</h1>
          <p className="text-slate-400 font-medium">Calculate the Broadcom/VMware licensing cost impact and compare against GCP migration savings.</p>
        </div>
        <button onClick={exportReport} className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white bg-indigo-600 border border-indigo-500/30 rounded-xl hover:bg-indigo-500 transition-all shadow-lg">
          <Download className="w-4 h-4" /> Export Analysis
        </button>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* Config */}
      <div className="flex gap-4 mb-8">
        <div className="bg-[#131826] rounded-xl p-4 border border-white/[0.05] flex items-center gap-3">
          <label className="text-xs text-slate-400 font-bold whitespace-nowrap">VMware Renewal Date</label>
          <input type="date" value={renewalDate} onChange={e => setRenewalDate(e.target.value)} className="bg-slate-900 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white" />
        </div>
        <div className="bg-[#131826] rounded-xl p-4 border border-white/[0.05] flex items-center gap-3">
          <label className="text-xs text-slate-400 font-bold whitespace-nowrap">Cores/Host</label>
          <input type="number" value={coresPerHost} onChange={e => setCoresPerHost(parseInt(e.target.value) || 32)} className="bg-slate-900 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white w-20" />
        </div>
      </div>

      {/* Urgency Banner */}
      <div className={`mb-8 p-5 rounded-xl border flex items-center gap-4 ${analysis.daysUntil < 180 ? 'bg-red-500/5 border-red-500/20' : 'bg-amber-500/5 border-amber-500/20'}`}>
        <Clock className={`w-8 h-8 ${analysis.daysUntil < 180 ? 'text-red-400' : 'text-amber-400'}`} />
        <div>
          <div className="text-lg font-bold text-white">{analysis.daysUntil} days until VMware renewal</div>
          <div className="text-sm text-slate-400">
            {analysis.daysUntil < 90 ? '🔴 CRITICAL — Migrate before renewal to avoid Broadcom pricing' :
             analysis.daysUntil < 180 ? '🟡 HIGH — Begin migration planning immediately' :
             '🟢 Plan migration before renewal date'}
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Old VMware Cost</div>
          <div className="text-3xl font-bold text-slate-300">{fmt(analysis.oldTotal)}<span className="text-sm text-slate-500">/yr</span></div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-red-500/20">
          <div className="text-sm text-slate-400 mb-1">New Broadcom Cost</div>
          <div className="text-3xl font-bold text-red-400">{fmt(analysis.newTotal)}<span className="text-sm text-slate-500">/yr</span></div>
          <div className="text-xs text-red-400 mt-1">+{analysis.priceIncrease}% increase</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-emerald-500/20">
          <div className="text-sm text-slate-400 mb-1">GCP with CUD</div>
          <div className="text-3xl font-bold text-emerald-400">{fmt(analysis.gcpWithCUD)}<span className="text-sm text-slate-500">/yr</span></div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.05)]">
          <div className="text-sm text-slate-400 mb-1">Annual Savings</div>
          <div className="text-3xl font-bold text-emerald-400">{fmt(analysis.savings)}</div>
          <div className="text-xs text-emerald-400 mt-1">{analysis.savingsPct}% vs Broadcom</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-lg font-bold text-white mb-4">Annual Cost Comparison</h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analysis.costBreakdown}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" /><XAxis dataKey="name" stroke="#64748b" tick={{fontSize:10}} /><YAxis stroke="#64748b" tick={{fontSize:11}} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} /><Tooltip contentStyle={{backgroundColor:'#0f172a', borderColor:'#1e293b', color:'#fff'}} formatter={v => [`$${v.toLocaleString()}`, 'Annual Cost']} /><Bar dataKey="cost" radius={[6,6,0,0]}>
                {analysis.costBreakdown.map((e, i) => <Cell key={i} fill={e.fill} />)}
              </Bar></BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-lg font-bold text-white mb-4">3-Year TCO Projection</h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analysis.projection}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" /><XAxis dataKey="year" stroke="#64748b" tick={{fontSize:11}} /><YAxis stroke="#64748b" tick={{fontSize:11}} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} /><Tooltip contentStyle={{backgroundColor:'#0f172a', borderColor:'#1e293b', color:'#fff'}} formatter={v => [`$${v.toLocaleString()}`, '']} /><Bar dataKey="vmware" name="Broadcom VMware" fill="#ef4444" radius={[4,4,0,0]} /><Bar dataKey="gcp" name="GCP Migration" fill="#10b981" radius={[4,4,0,0]} /></BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Summary Card */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><TrendingDown className="w-5 h-5 text-emerald-400" /> Migration ROI Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5"><div className="text-xs text-slate-400 mb-1">Migration Cost</div><div className="text-xl font-bold">{fmt(analysis.migrationCost)}</div></div>
          <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5"><div className="text-xs text-slate-400 mb-1">Break-Even</div><div className="text-xl font-bold">{analysis.monthlyBreakeven} months</div></div>
          <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5"><div className="text-xs text-slate-400 mb-1">3-Year Savings</div><div className="text-xl font-bold text-emerald-400">{fmt(analysis.savings * 3)}</div></div>
          <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5"><div className="text-xs text-slate-400 mb-1">Environment</div><div className="text-xl font-bold">{analysis.estimatedHosts} hosts / {analysis.totalVMs.toLocaleString()} VMs</div></div>
        </div>
      </div>
    </main>
  );
}
