import React, { useEffect, useState, useMemo } from 'react';
import api from '../lib/api';
import axios from 'axios';
import { Leaf, Factory, Car, TreePine, Zap, Download, Globe2 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, PieChart, Pie } from 'recharts';

const GCP_REGIONS = {
  'us-central1': { name: 'Iowa', cfe: 97, pue: 1.10 },
  'europe-west1': { name: 'Belgium', cfe: 97, pue: 1.10 },
  'asia-south1': { name: 'Mumbai', cfe: 36, pue: 1.12 },
  'us-east1': { name: 'South Carolina', cfe: 53, pue: 1.09 },
  'europe-north1': { name: 'Finland', cfe: 97, pue: 1.08 },
  'australia-southeast1': { name: 'Sydney', cfe: 28, pue: 1.12 },
};

export default function CarbonFootprint() {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [targetRegion, setTargetRegion] = useState('us-central1');
  const [onPremPUE, setOnPremPUE] = useState(1.8);

  useEffect(() => {
    api.get('/api/inventory/servers')
      .then(res => setServers(res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const analysis = useMemo(() => {
    const region = GCP_REGIONS[targetRegion];
    const totalVCPUs = servers.reduce((s, sv) => s + (sv.vcpu || 4), 0);
    
    // On-prem calculation
    const wattsPerVCPU = 12; // ~12W per vCPU average
    const totalKW = (totalVCPUs * wattsPerVCPU) / 1000;
    const effectiveKW = totalKW * onPremPUE;
    const hoursPerYear = 8760;
    const onPremMWh = (effectiveKW * hoursPerYear) / 1000;
    const gridEmissionFactor = 0.42; // tonnes CO2e per MWh (global average)
    const onPremCO2 = Math.round(onPremMWh * gridEmissionFactor);

    // GCP calculation
    const gcpEffectiveKW = totalKW * region.pue;
    const gcpMWh = (gcpEffectiveKW * hoursPerYear) / 1000;
    const gcpCO2 = Math.round(gcpMWh * gridEmissionFactor * (1 - region.cfe / 100));

    const reduction = onPremCO2 - gcpCO2;
    const reductionPct = onPremCO2 > 0 ? Math.round((reduction / onPremCO2) * 100) : 0;
    const carsEquivalent = Math.round(reduction / 4.6); // 4.6 tonnes per car per year
    const treesEquivalent = Math.round(reduction * 45); // ~45 trees per tonne CO2
    const homesEquivalent = Math.round(reduction / 7.5); // 7.5 tonnes per home per year

    const comparison = [
      { name: 'On-Premises', co2: onPremCO2, fill: '#ef4444' },
      { name: `GCP (${region.name})`, co2: gcpCO2, fill: '#10b981' },
    ];

    const regionComparison = Object.entries(GCP_REGIONS).map(([id, r]) => ({
      name: r.name,
      co2: Math.round(gcpMWh * gridEmissionFactor * (1 - r.cfe / 100)),
      cfe: r.cfe,
      fill: id === targetRegion ? '#10b981' : '#6366f1',
    }));

    return {
      totalVCPUs, totalKW: effectiveKW, onPremMWh, onPremCO2,
      gcpCO2, reduction, reductionPct, carsEquivalent, treesEquivalent, homesEquivalent,
      region, comparison, regionComparison
    };
  }, [servers, targetRegion, onPremPUE]);

  const exportReport = () => {
    let r = `# D.A.M.I. Carbon Footprint Impact Report\n_Generated: ${new Date().toLocaleString()}_\n\n`;
    r += `## Executive Summary\nMigrating ${servers.length.toLocaleString()} servers to GCP ${analysis.region.name} reduces carbon emissions by **${analysis.reductionPct}%**.\n\n`;
    r += `## Carbon Analysis\n| Metric | On-Premises | GCP (${analysis.region.name}) |\n|--------|-------------|--------|\n`;
    r += `| Annual CO₂ Emissions | ${analysis.onPremCO2} tonnes | ${analysis.gcpCO2} tonnes |\n`;
    r += `| Carbon-Free Energy | ~0% | ${analysis.region.cfe}% |\n`;
    r += `| PUE | ${onPremPUE} | ${analysis.region.pue} |\n\n`;
    r += `## Environmental Impact\n- **${analysis.reduction} tonnes CO₂** reduced annually\n- Equivalent to **${analysis.carsEquivalent} cars** removed from the road\n- Equivalent to planting **${analysis.treesEquivalent.toLocaleString()} trees**\n`;
    const blob = new Blob([r], { type: 'text/markdown' }); const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = `DAMI_Carbon_Footprint_${new Date().toISOString().slice(0,10)}.md`; a.click();
  };

  if (loading) return <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full"><div className="text-emerald-400 text-xl font-bold animate-pulse">Calculating Carbon Impact...</div></main>;

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-400 tracking-tight mb-2">Carbon Footprint Report</h1>
          <p className="text-slate-400 font-medium">ESG impact analysis — calculate carbon reduction from migrating on-premises infrastructure to GCP.</p>
        </div>
        <button onClick={exportReport} className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white bg-emerald-600 border border-emerald-500/30 rounded-xl hover:bg-emerald-500 transition-all shadow-lg">
          <Download className="w-4 h-4" /> Export ESG Report
        </button>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* Config */}
      <div className="flex gap-4 mb-8 flex-wrap">
        <div className="bg-[#131826] rounded-xl p-4 border border-white/[0.05] flex items-center gap-3">
          <Globe2 className="w-4 h-4 text-emerald-400" />
          <label className="text-xs text-slate-400 font-bold">Target GCP Region</label>
          <select value={targetRegion} onChange={e => setTargetRegion(e.target.value)} className="bg-slate-900 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white">
            {Object.entries(GCP_REGIONS).map(([id, r]) => <option key={id} value={id}>{r.name} ({r.cfe}% CFE)</option>)}
          </select>
        </div>
        <div className="bg-[#131826] rounded-xl p-4 border border-white/[0.05] flex items-center gap-3">
          <Factory className="w-4 h-4 text-slate-400" />
          <label className="text-xs text-slate-400 font-bold">On-Prem PUE</label>
          <input type="number" step="0.1" value={onPremPUE} onChange={e => setOnPremPUE(parseFloat(e.target.value) || 1.8)} className="bg-slate-900 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white w-20" />
        </div>
      </div>

      {/* Hero Impact Banner */}
      <div className="bg-gradient-to-r from-emerald-900/20 to-teal-900/20 rounded-2xl p-8 border border-emerald-500/20 mb-8 relative overflow-hidden">
        <Leaf className="absolute -right-8 -top-8 w-40 h-40 text-emerald-500/5" />
        <div className="text-center relative z-10">
          <div className="text-7xl font-black text-emerald-400 mb-2">{analysis.reductionPct}%</div>
          <div className="text-xl font-bold text-white mb-4">Carbon Reduction</div>
          <div className="flex justify-center gap-8 flex-wrap">
            <div className="flex items-center gap-2"><Car className="w-5 h-5 text-amber-400" /><span className="text-sm"><strong className="text-white">{analysis.carsEquivalent.toLocaleString()}</strong> <span className="text-slate-400">cars off the road</span></span></div>
            <div className="flex items-center gap-2"><TreePine className="w-5 h-5 text-emerald-400" /><span className="text-sm"><strong className="text-white">{analysis.treesEquivalent.toLocaleString()}</strong> <span className="text-slate-400">trees planted equivalent</span></span></div>
            <div className="flex items-center gap-2"><Zap className="w-5 h-5 text-blue-400" /><span className="text-sm"><strong className="text-white">{analysis.reduction}</strong> <span className="text-slate-400">tonnes CO₂/year saved</span></span></div>
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">On-Premises CO₂</div>
          <div className="text-3xl font-bold text-red-400">{analysis.onPremCO2}<span className="text-sm text-slate-500"> t/yr</span></div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-emerald-500/20">
          <div className="text-sm text-slate-400 mb-1">GCP CO₂</div>
          <div className="text-3xl font-bold text-emerald-400">{analysis.gcpCO2}<span className="text-sm text-slate-500"> t/yr</span></div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">GCP Carbon-Free Energy</div>
          <div className="text-3xl font-bold text-emerald-400">{analysis.region.cfe}%</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Power Usage (On-Prem)</div>
          <div className="text-3xl font-bold text-white">{analysis.totalKW.toFixed(0)}<span className="text-sm text-slate-500"> kW</span></div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-lg font-bold text-white mb-4">CO₂ Comparison</h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analysis.comparison}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" /><XAxis dataKey="name" stroke="#64748b" tick={{fontSize:11}} /><YAxis stroke="#64748b" tick={{fontSize:11}} /><Tooltip contentStyle={{backgroundColor:'#0f172a', borderColor:'#1e293b', color:'#fff'}} formatter={v => [`${v} tonnes CO₂/yr`, 'Emissions']} /><Bar dataKey="co2" radius={[6,6,0,0]}>{analysis.comparison.map((e, i) => <Cell key={i} fill={e.fill} />)}</Bar></BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-lg font-bold text-white mb-4">GCP Region Comparison</h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analysis.regionComparison}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" /><XAxis dataKey="name" stroke="#64748b" tick={{fontSize:10}} /><YAxis stroke="#64748b" tick={{fontSize:11}} /><Tooltip contentStyle={{backgroundColor:'#0f172a', borderColor:'#1e293b', color:'#fff'}} formatter={(v, n, p) => [`${v} tonnes CO₂/yr (${p.payload.cfe}% CFE)`, 'Emissions']} /><Bar dataKey="co2" radius={[6,6,0,0]}>{analysis.regionComparison.map((e, i) => <Cell key={i} fill={e.fill} />)}</Bar></BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </main>
  );
}
