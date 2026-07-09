import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { Key, AlertTriangle, Clock, ShieldCheck } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, PieChart, Pie } from 'recharts';

const EOL_RISK = {
  'Windows Server 2008 R2': { eol: '2020-01-14', risk: 'critical' },
  'Windows Server 2012': { eol: '2023-10-10', risk: 'critical' },
  'CentOS 7': { eol: '2024-06-30', risk: 'high' },
  'Red Hat Enterprise Linux 7': { eol: '2024-06-30', risk: 'high' },
  'Ubuntu Linux 18.04': { eol: '2023-06-01', risk: 'high' },
  'Windows Server 2016': { eol: '2027-01-12', risk: 'medium' },
  'Red Hat Enterprise Linux 8': { eol: '2029-05-31', risk: 'low' },
  'Ubuntu Linux 20.04': { eol: '2025-04-02', risk: 'medium' },
  'Ubuntu Linux 22.04': { eol: '2027-04-01', risk: 'low' },
};

const RISK_COLORS = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e' };

export default function LicenseRisk() {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:8000/api/inventory/servers')
      .then(res => setServers(res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Analyze each server's OS against EOL
  const analyzed = useMemo(() => {
    return servers.map(s => {
      const eolInfo = Object.entries(EOL_RISK).find(([os]) => s.os?.includes(os.replace(/ \(.*\)/, '')));
      return {
        ...s,
        eol_date: eolInfo ? eolInfo[1].eol : 'Unknown',
        eol_risk: eolInfo ? eolInfo[1].risk : 'low'
      };
    });
  }, [servers]);

  const riskCounts = useMemo(() => {
    const counts = { critical: 0, high: 0, medium: 0, low: 0 };
    analyzed.forEach(s => counts[s.eol_risk] = (counts[s.eol_risk] || 0) + 1);
    return counts;
  }, [analyzed]);

  const osCounts = useMemo(() => {
    const counts = {};
    analyzed.forEach(s => { counts[s.os] = (counts[s.os] || 0) + 1; });
    return Object.entries(counts).map(([name, value]) => ({ name: name?.substring(0, 30), value }));
  }, [analyzed]);

  const riskPieData = Object.entries(riskCounts).map(([name, value]) => ({ name, value }));

  if (loading) return <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full"><div className="text-indigo-400 text-xl font-bold animate-pulse">Analyzing License Risk...</div></main>;

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">License Risk & EOL Analysis</h1>
        <p className="text-slate-400 font-medium">Identify operating systems approaching or past End-of-Life, creating licensing and security vulnerabilities during migration.</p>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {Object.entries(riskCounts).map(([level, count]) => (
          <div key={level} className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
            <div className="text-sm text-slate-400 capitalize mb-1">{level} Risk</div>
            <div className="text-3xl font-bold" style={{ color: RISK_COLORS[level] }}>{count} VMs</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-xl font-bold text-white mb-4">EOL Risk Distribution</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart><Pie data={riskPieData} cx="50%" cy="50%" innerRadius={60} outerRadius={110} paddingAngle={2} dataKey="value" label={({name, percent}) => `${name} ${(percent*100).toFixed(0)}%`}>
                {riskPieData.map((e, i) => <Cell key={i} fill={RISK_COLORS[e.name]} />)}
              </Pie><Tooltip contentStyle={{backgroundColor:'#0f172a', borderColor:'#1e293b', color:'#fff'}} /></PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-xl font-bold text-white mb-4">OS Distribution</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={osCounts} margin={{ left: 100 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" stroke="#64748b" tick={{fontSize:11}} />
                <YAxis type="category" dataKey="name" stroke="#64748b" tick={{fontSize:10, fill:'#cbd5e1'}} width={100} />
                <Tooltip contentStyle={{backgroundColor:'#0f172a', borderColor:'#1e293b', color:'#fff'}} />
                <Bar dataKey="value" fill="#6366f1" barSize={14} radius={[0,4,4,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
        <h3 className="text-xl font-bold text-white mb-4">Detailed EOL Risk Register</h3>
        <div className="overflow-x-auto max-h-[400px] custom-scrollbar">
          <table className="w-full text-xs text-left">
            <thead className="text-slate-400 bg-slate-900 border-b border-white/10 sticky top-0 z-10">
              <tr><th className="p-3">Server</th><th className="p-3">OS</th><th className="p-3">EOL Date</th><th className="p-3">Risk</th><th className="p-3">Environment</th></tr>
            </thead>
            <tbody className="text-slate-300 divide-y divide-white/5 bg-[#0f141f]">
              {analyzed.filter(s => s.eol_risk === 'critical' || s.eol_risk === 'high').map((s, i) => (
                <tr key={i} className="hover:bg-white/5">
                  <td className="p-3 font-medium text-indigo-300">{s.name}</td>
                  <td className="p-3">{s.os}</td>
                  <td className="p-3 font-mono">{s.eol_date}</td>
                  <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-xs font-bold ${s.eol_risk === 'critical' ? 'bg-red-500/10 text-red-400' : 'bg-orange-500/10 text-orange-400'}`}>{s.eol_risk}</span></td>
                  <td className="p-3">{s.environment}</td>
                </tr>
              ))}
              {analyzed.filter(s => s.eol_risk === 'critical' || s.eol_risk === 'high').length === 0 && <tr><td colSpan="5" className="p-4 text-center text-emerald-400">No critical/high EOL risks detected!</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
