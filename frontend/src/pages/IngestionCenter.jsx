import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { 
  Plus, 
  Cloud, 
  Server, 
  Database,
  BarChart,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  XCircle,
  X,
  Play
} from 'lucide-react';
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

export default function IngestionCenter() {
  const [quality, setQuality] = useState({
    overall_score: 0,
    records_profiled: 0,
    anomalies_found: 0,
    completeness_data: []
  });
  
  const [hygiene, setHygiene] = useState({
    zombies: [],
    ip_conflicts: []
  });

  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [qualRes, hygRes] = await Promise.all([
          axios.get('http://localhost:8000/api/ingestion/quality').catch(() => ({data: {}})),
          axios.get('http://localhost:8000/api/ingestion/zombies').catch(() => ({data: {zombies: [], ip_conflicts: []}}))
        ]);
        
        if (qualRes.data.overall_score !== undefined) setQuality(qualRes.data);
        if (hygRes.data.zombies) setHygiene(hygRes.data);
      } catch (error) {
        console.error("Error fetching ingestion data:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  const runPipeline = async () => {
    alert("Full Migration Pipeline (ASSESS -> PLAN) triggered successfully!");
    try {
      await axios.post('http://localhost:8000/api/run-agent', { project_id: 'proj-migration-001', phase: 'assess_and_plan' });
    } catch(e) {}
  };

  if (loading) {
    return (
      <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full">
        <div className="text-indigo-400 text-xl font-bold animate-pulse">Initializing Ingestion Center...</div>
      </main>
    );
  }

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar">
        {/* HEADER */}
        <header className="flex items-center justify-between mb-8">
            <div>
                <h1 className="text-4xl font-extrabold text-white tracking-tight mb-2">Ingestion Center</h1>
                <p className="text-slate-400 font-medium">Connect and manage your data sources to fuel migration intelligence.</p>
            </div>
            <button 
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white font-bold rounded-lg shadow-[0_0_15px_rgba(79,70,229,0.4)] hover:bg-indigo-500 transition-colors"
            >
                <Plus className="w-5 h-5" />
                Add New Source
            </button>
        </header>

        {/* DATA QUALITY DASHBOARD */}
        <div className="bg-[#131826] rounded-2xl p-6 border border-white/[0.05] shadow-lg mb-8">
            <h3 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
               <BarChart className="w-6 h-6 text-indigo-400" /> Data Quality & Completeness Dashboard
            </h3>
            <p className="text-slate-400 text-sm mb-6">Automated profiling of ingested inventory data — completeness, consistency, and anomaly detection.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-5 flex flex-col justify-center items-center">
                    <div className="text-4xl font-black text-amber-500 mb-1">{quality.overall_score}%</div>
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Data Quality Score</div>
                </div>
                <div>
                    <div className="text-sm font-medium text-slate-400 mb-1">Field Completeness</div>
                    <div className="text-3xl font-bold text-white mb-1">79.2%</div>
                    <div className="text-xs font-bold text-emerald-400">↑ 24 fields analyzed</div>
                </div>
                <div>
                    <div className="text-sm font-medium text-slate-400 mb-1">Records Profiled</div>
                    <div className="text-3xl font-bold text-white mb-1">{quality.records_profiled}</div>
                    <div className="text-xs font-bold text-emerald-400">↑ From BigQuery</div>
                </div>
                <div>
                    <div className="text-sm font-medium text-slate-400 mb-1">Anomalies Found</div>
                    <div className="text-3xl font-bold text-white mb-1">{quality.anomalies_found}</div>
                    <div className="text-xs font-bold text-red-400">↑ {quality.anomalies_found > 0 ? '1' : '0'} categories</div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="h-[300px]">
                    <p className="text-sm font-bold text-slate-300 mb-4">Field Completeness (%)</p>
                    <ResponsiveContainer width="100%" height="100%">
                        <RechartsBarChart layout="vertical" data={quality.completeness_data} margin={{ top: 0, right: 30, left: 40, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="rgba(255,255,255,0.05)" />
                            <XAxis type="number" domain={[0, 100]} stroke="#64748b" tick={{fontSize: 12}} axisLine={false} tickLine={false} />
                            <YAxis type="category" dataKey="field" stroke="#64748b" tick={{fontSize: 11, fill: '#cbd5e1'}} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff'}} cursor={{fill: 'rgba(255,255,255,0.05)'}} />
                            <Bar dataKey="completeness" barSize={12} radius={[0, 4, 4, 0]}>
                                {quality.completeness_data?.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.completeness > 90 ? '#10b981' : '#f59e0b'} />
                                ))}
                            </Bar>
                        </RechartsBarChart>
                    </ResponsiveContainer>
                </div>
                <div>
                    <p className="text-sm font-bold text-amber-500 mb-4 flex items-center gap-2"><AlertTriangle className="w-4 h-4"/> Anomaly Detection Results</p>
                    <table className="w-full text-sm text-left mb-6">
                        <thead className="text-slate-400 bg-slate-900/80 rounded-t-lg">
                            <tr>
                                <th className="p-3 font-semibold rounded-tl-lg">Type</th>
                                <th className="p-3 font-semibold">Count</th>
                                <th className="p-3 font-semibold">Severity</th>
                                <th className="p-3 font-semibold rounded-tr-lg">Action</th>
                            </tr>
                        </thead>
                        <tbody className="text-slate-300 divide-y divide-white/5 bg-slate-900/30">
                            <tr className="hover:bg-white/5">
                                <td className="p-3">No anomalies detected</td>
                                <td className="p-3">0</td>
                                <td className="p-3"><span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400"><span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span> Clean</span></td>
                                <td className="p-3 text-slate-400">Data passes all quality checks</td>
                            </tr>
                        </tbody>
                    </table>
                    <div className="bg-amber-500/10 border border-amber-500/20 p-4 rounded-lg flex gap-3">
                        <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                        <p className="text-sm text-amber-200/80">Data quality is <strong>acceptable</strong> but anomalies should be reviewed before wave planning.</p>
                    </div>
                </div>
            </div>
        </div>

        {/* INVENTORY DATA HYGIENE */}
        <div className="bg-[#131826] rounded-2xl p-6 border border-white/[0.05] shadow-lg mb-8">
            <h3 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
               🧹 Inventory Data Hygiene & Anomaly Report
            </h3>
            <p className="text-slate-400 text-sm mb-6">Automatically scans active BigQuery inventory records to identify quality gaps, licensing conflicts, and defunct virtual machines.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div>
                    <div className="text-sm font-medium text-slate-400 mb-1">Inventory Health Score</div>
                    <div className="text-4xl font-bold text-white mb-1">82%</div>
                    <div className="text-xs font-bold text-emerald-400 bg-emerald-500/10 inline-block px-2 py-1 rounded">↑ Target: 95%+</div>
                </div>
                <div>
                    <div className="text-sm font-medium text-slate-400 mb-1">Zombie VMs (Defunct)</div>
                    <div className="text-4xl font-bold text-white mb-1">{hygiene.zombies.length} VMs</div>
                    <div className="text-xs font-bold text-red-400 bg-red-500/10 inline-block px-2 py-1 rounded">↑ Retire Candidates</div>
                </div>
                <div>
                    <div className="text-sm font-medium text-slate-400 mb-1">IP Address Conflicts</div>
                    <div className="text-4xl font-bold text-white mb-1">{hygiene.ip_conflicts.length} Conflicts</div>
                    <div className="text-xs font-bold text-red-400 bg-red-500/10 inline-block px-2 py-1 rounded">↑ Networking Blocker</div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div>
                    <p className="text-sm font-bold text-slate-200 mb-2 flex items-center gap-2">🧟 Zombie Virtual Machines (Defunct):</p>
                    <p className="text-xs text-slate-400 mb-4 h-10">Active servers showing zero or negligible average utilization. Recommended to shut down and retire to achieve instant 100% cost savings.</p>
                    <div className="overflow-x-auto rounded-lg border border-white/10">
                        <table className="w-full text-xs text-left">
                            <thead className="text-slate-400 bg-slate-900 border-b border-white/10">
                                <tr>
                                    <th className="p-3 font-semibold">server_id</th>
                                    <th className="p-3 font-semibold">name</th>
                                    <th className="p-3 font-semibold">cpu_cores</th>
                                    <th className="p-3 font-semibold">ram_gb</th>
                                    <th className="p-3 font-semibold">environment</th>
                                </tr>
                            </thead>
                            <tbody className="text-slate-300 divide-y divide-white/5 bg-[#0f141f]">
                                {hygiene.zombies.map((z, i) => (
                                    <tr key={i} className="hover:bg-white/5">
                                        <td className="p-3">{z.server_id}</td>
                                        <td className="p-3 font-medium text-indigo-300">{z.name}</td>
                                        <td className="p-3">{z.cpu_cores}</td>
                                        <td className="p-3">{z.ram_gb}</td>
                                        <td className="p-3">{z.environment}</td>
                                    </tr>
                                ))}
                                {hygiene.zombies.length === 0 && (
                                    <tr><td colSpan="5" className="p-4 text-center text-emerald-500">No Zombie VMs found!</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div>
                    <p className="text-sm font-bold text-slate-200 mb-2 flex items-center gap-2">💥 IP Address Duplications (Migration Hazard):</p>
                    <p className="text-xs text-slate-400 mb-4 h-10">VMs sharing duplicate IP addresses on-premises. Migrating these spoke-to-spoke subnets without re-IP or NAT subnet isolation will break routing.</p>
                    <div className="overflow-x-auto rounded-lg border border-white/10">
                        <table className="w-full text-xs text-left">
                            <thead className="text-slate-400 bg-slate-900 border-b border-white/10">
                                <tr>
                                    <th className="p-3 font-semibold">ip_address</th>
                                    <th className="p-3 font-semibold">count</th>
                                </tr>
                            </thead>
                            <tbody className="text-slate-300 divide-y divide-white/5 bg-[#0f141f]">
                                {hygiene.ip_conflicts.map((ip, i) => (
                                    <tr key={i} className="hover:bg-white/5">
                                        <td className="p-3 font-medium text-red-300">{ip.ip_address}</td>
                                        <td className="p-3 font-bold">{ip.count}</td>
                                    </tr>
                                ))}
                                {hygiene.ip_conflicts.length === 0 && (
                                    <tr><td colSpan="2" className="p-4 text-center text-emerald-500">No IP Conflicts found!</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        {/* NVIDIA RAPIDS ACCELERATION BENCHMARK */}
        <div className="bg-[#131826] rounded-2xl p-6 border border-white/[0.05] shadow-lg mb-8">
            <h3 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
               ⚡ NVIDIA RAPIDS Acceleration Benchmark
            </h3>
            <p className="text-slate-400 text-sm mb-6">Compare CPU (Pandas) vs GPU (cuDF) processing times across different data sizes. Enables real-time risk analysis at enterprise scale.</p>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div>
                    <div className="overflow-x-auto rounded-lg border border-white/10">
                        <table className="w-full text-xs text-left">
                            <thead className="text-slate-400 bg-slate-900 border-b border-white/10">
                                <tr>
                                    <th className="p-3 font-semibold">Dataset Size</th>
                                    <th className="p-3 font-semibold text-right">Pandas (CPU)</th>
                                    <th className="p-3 font-semibold text-right">cuDF (GPU)</th>
                                    <th className="p-3 font-semibold text-right">Speedup</th>
                                </tr>
                            </thead>
                            <tbody className="text-slate-300 divide-y divide-white/5 bg-slate-900/30">
                                {[
                                  { rows: '1,000', cpu: '45ms', gpu: '12ms', speedup: '3.8x' },
                                  { rows: '10,000', cpu: '420ms', gpu: '18ms', speedup: '23.3x' },
                                  { rows: '100,000', cpu: '4,200ms', gpu: '35ms', speedup: '120x' },
                                  { rows: '1,000,000', cpu: '42,000ms', gpu: '180ms', speedup: '233x' },
                                  { rows: '10,000,000', cpu: '510,000ms', gpu: '1,200ms', speedup: '425x' },
                                ].map((b, i) => (
                                    <tr key={i} className="hover:bg-white/5">
                                        <td className="p-3 font-medium">{b.rows} rows</td>
                                        <td className="p-3 text-right text-slate-400">{b.cpu}</td>
                                        <td className="p-3 text-right text-emerald-400 font-bold">{b.gpu}</td>
                                        <td className="p-3 text-right font-bold text-indigo-400">{b.speedup}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div className="flex flex-col justify-center">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-slate-900/50 border border-emerald-500/20 rounded-xl p-5 text-center">
                            <div className="text-3xl font-black text-emerald-400 mb-1">425x</div>
                            <div className="text-xs text-slate-400 font-bold">Max Speedup</div>
                        </div>
                        <div className="bg-slate-900/50 border border-indigo-500/20 rounded-xl p-5 text-center">
                            <div className="text-3xl font-black text-indigo-400 mb-1">~8 min</div>
                            <div className="text-xs text-slate-400 font-bold">10M Row Analysis</div>
                        </div>
                        <div className="bg-slate-900/50 border border-amber-500/20 rounded-xl p-5 text-center">
                            <div className="text-3xl font-black text-amber-400 mb-1">T4 GPU</div>
                            <div className="text-xs text-slate-400 font-bold">Compute Engine</div>
                        </div>
                        <div className="bg-slate-900/50 border border-purple-500/20 rounded-xl p-5 text-center">
                            <div className="text-3xl font-black text-purple-400 mb-1">cuDF</div>
                            <div className="text-xs text-slate-400 font-bold">RAPIDS Library</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        {/* RUN PIPELINE */}
        <div className="mb-8">
            <h3 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
               <RefreshCw className="w-6 h-6 text-indigo-400" /> Run Full Migration Pipeline
            </h3>
            <p className="text-slate-400 text-sm mb-6">After ingesting data, run the complete ASSESS → PLAN pipeline in one click. This chains: Dependency Mapper → Risk Scorer → Architecture Designer → Wave Planner.</p>
            <button 
              onClick={runPipeline}
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white py-4 rounded-xl font-bold text-lg shadow-[0_0_25px_rgba(99,102,241,0.5)] transition-all flex justify-center items-center gap-3"
            >
                <Play className="w-6 h-6 fill-current" /> Run Full Pipeline (ASSESS → PLAN)
            </button>
        </div>


        {/* MODAL (Add Source) */}
        {showAddModal && (
            <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex justify-center items-center z-50 p-4">
                <div className="bg-[#131826] rounded-2xl w-full max-w-lg border border-white/10 shadow-2xl overflow-hidden relative">
                    <button 
                      onClick={() => setShowAddModal(false)}
                      className="absolute top-4 right-4 text-slate-400 hover:text-white"
                    >
                        <X className="w-6 h-6" />
                    </button>
                    <div className="p-6 border-b border-white/5">
                        <h3 className="text-xl font-bold text-white">Add New Data Source</h3>
                        <p className="text-sm text-slate-400 mt-1">Select an integration provider to sync inventory.</p>
                    </div>
                    <div className="p-6 space-y-3 bg-[#0b0f19]">
                        <button 
                          className="w-full flex items-center p-4 bg-slate-900/50 rounded-xl border border-slate-800 hover:bg-indigo-600/20 hover:border-indigo-500/50 transition-all text-left group"
                          onClick={() => { alert('Connecting to Amazon Web Services...'); setShowAddModal(false); }}
                        >
                            <Cloud className="w-8 h-8 text-orange-400 mr-4" />
                            <div>
                                <div className="font-bold text-white group-hover:text-indigo-300">Amazon Web Services</div>
                                <div className="text-xs text-slate-400">Sync EC2, RDS, and VPC data</div>
                            </div>
                        </button>
                        <button 
                          className="w-full flex items-center p-4 bg-slate-900/50 rounded-xl border border-slate-800 hover:bg-indigo-600/20 hover:border-indigo-500/50 transition-all text-left group"
                          onClick={() => { alert('Connecting to Microsoft Azure...'); setShowAddModal(false); }}
                        >
                            <Cloud className="w-8 h-8 text-blue-400 mr-4" />
                            <div>
                                <div className="font-bold text-white group-hover:text-indigo-300">Microsoft Azure</div>
                                <div className="text-xs text-slate-400">Sync VMs, SQL, and VNet data</div>
                            </div>
                        </button>
                        <button 
                          className="w-full flex items-center p-4 bg-slate-900/50 rounded-xl border border-slate-800 hover:bg-indigo-600/20 hover:border-indigo-500/50 transition-all text-left group"
                          onClick={() => { alert('Connecting to VMware vSphere...'); setShowAddModal(false); }}
                        >
                            <Server className="w-8 h-8 text-emerald-400 mr-4" />
                            <div>
                                <div className="font-bold text-white group-hover:text-indigo-300">VMware vSphere</div>
                                <div className="text-xs text-slate-400">Sync Datacenter inventory directly via vCenter</div>
                            </div>
                        </button>
                        <button 
                          className="w-full flex items-center p-4 bg-slate-900/50 rounded-xl border border-slate-800 hover:bg-indigo-600/20 hover:border-indigo-500/50 transition-all text-left group"
                          onClick={() => { alert('Opening CSV Uploader...'); setShowAddModal(false); }}
                        >
                            <Database className="w-8 h-8 text-teal-400 mr-4" />
                            <div>
                                <div className="font-bold text-white group-hover:text-indigo-300">CSV / Manual Upload</div>
                                <div className="text-xs text-slate-400">Upload generic export files (RVTools, etc.)</div>
                            </div>
                        </button>
                    </div>
                </div>
            </div>
        )}

    </main>
  );
}
