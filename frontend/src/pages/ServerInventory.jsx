import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { 
  ServerCog, Cpu, MemoryStick, Database, Search, Plus, Filter, ArrowDownUp 
} from 'lucide-react';
import {
  PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Treemap,
} from 'recharts';

const OS_COLORS = ['#38bdf8', '#facc15', '#f87171', '#4ade80', '#a78bfa', '#fb923c', '#94a3b8'];
const WORKLOAD_COLORS = ['#f59e0b', '#3b82f6', '#10b981', '#6366f1', '#ec4899', '#14b8a6', '#f43f5e'];

const PAGE_SIZE = 50;

export default function ServerInventory() {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  
  // Filters
  const [envFilter, setEnvFilter] = useState("All");
  const [workloadFilter, setWorkloadFilter] = useState("All");
  const [stateFilter, setStateFilter] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const fetchServers = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/inventory/servers');
        setServers(res.data || []);
      } catch (error) {
        console.error("Error fetching servers:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchServers();
  }, []);

  // Filtered Data
  const filteredServers = useMemo(() => {
    setPage(0); // Reset pagination when filters change
    return servers.filter(s => {
      const matchEnv = envFilter === "All" || s.environment === envFilter;
      const matchWorkload = workloadFilter === "All" || s.workload_type === workloadFilter;
      const matchState = stateFilter === "All" || s.power_state === stateFilter;
      const matchSearch = searchQuery === "" || 
        s.name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
        s.ip_address?.toLowerCase().includes(searchQuery.toLowerCase());
      return matchEnv && matchWorkload && matchState && matchSearch;
    });
  }, [servers, envFilter, workloadFilter, stateFilter, searchQuery]);

  // Derived Options
  const envs = ["All", ...Array.from(new Set(servers.map(s => s.environment))).sort()];
  const workloads = ["All", ...Array.from(new Set(servers.map(s => s.workload_type))).sort()];
  const states = ["All", ...Array.from(new Set(servers.map(s => s.power_state))).sort()];

  // KPIs
  const activeVMs = filteredServers.filter(s => s.power_state === 'poweredOn');
  const totalCpus = filteredServers.reduce((sum, s) => sum + (s.vcpu || 0), 0);
  const avgCpu = activeVMs.length ? activeVMs.reduce((sum, s) => sum + (s.cpu_utilization_avg || 0), 0) / activeVMs.length : 0;
  const avgRam = activeVMs.length ? activeVMs.reduce((sum, s) => sum + (s.ram_utilization_avg || 0), 0) / activeVMs.length : 0;

  // OS Chart Data
  const osData = useMemo(() => {
    const counts = filteredServers.reduce((acc, s) => {
      acc[s.os] = (acc[s.os] || 0) + 1;
      return acc;
    }, {});
    return Object.keys(counts).map(os => ({ name: os, value: counts[os] })).sort((a,b) => b.value - a.value);
  }, [filteredServers]);

  // Workload Chart Data
  const workloadData = useMemo(() => {
    const counts = filteredServers.reduce((acc, s) => {
      acc[s.workload_type] = (acc[s.workload_type] || 0) + 1;
      return acc;
    }, {});
    return Object.keys(counts).map(w => ({ name: w, count: counts[w] }));
  }, [filteredServers]);

  // Treemap Data
  const treemapData = useMemo(() => {
    const grouped = filteredServers.filter(s => s.vcpu > 0).reduce((acc, s) => {
      if (!acc[s.workload_type]) acc[s.workload_type] = { name: s.workload_type, children: [] };
      acc[s.workload_type].children.push({ name: s.name, size: s.vcpu, ram: s.ram_gb });
      return acc;
    }, {});
    return Object.values(grouped);
  }, [filteredServers]);
  
  // Heatmap Color scale helper
  const getHeatmapColor = (val) => {
      if (val === undefined || val === null) return '#0f141f';
      if (val < 20) return '#1e40af'; // Blue
      if (val < 40) return '#4f46e5'; // Indigo
      if (val < 60) return '#7c3aed'; // Purple
      if (val < 80) return '#f59e0b'; // Amber
      return '#ef4444'; // Red
  };

  if (loading) {
    return (
      <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full">
        <div className="text-indigo-400 text-xl font-bold animate-pulse">Loading Inventory Data...</div>
      </main>
    );
  }

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      
      {/* HEADER & FILTERS */}
      <header className="mb-8">
          <div className="flex justify-between items-end mb-6">
              <div>
                  <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Discovered Server Inventory</h1>
                  <p className="text-slate-400 font-medium">Browse and filter the complete catalog of discovered servers in your on-premises environment.</p>
              </div>
          </div>
          <div className="h-px bg-white/10 w-full mb-6"></div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Environment</label>
                  <select 
                    value={envFilter} 
                    onChange={e => setEnvFilter(e.target.value)}
                    className="w-full bg-[#131826] border border-white/10 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                      {envs.map(e => <option key={e} value={e}>{e}</option>)}
                  </select>
              </div>
              <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Workload Type</label>
                  <select 
                    value={workloadFilter} 
                    onChange={e => setWorkloadFilter(e.target.value)}
                    className="w-full bg-[#131826] border border-white/10 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                      {workloads.map(w => <option key={w} value={w}>{w}</option>)}
                  </select>
              </div>
              <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Power State</label>
                  <select 
                    value={stateFilter} 
                    onChange={e => setStateFilter(e.target.value)}
                    className="w-full bg-[#131826] border border-white/10 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                      {states.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
              </div>
              <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Search VM Name / IP</label>
                  <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input 
                        type="text" 
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        placeholder="Search..." 
                        className="w-full bg-[#131826] border border-white/10 rounded-lg pl-9 p-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                      />
                  </div>
              </div>
          </div>
      </header>

      {/* KPI STATS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div>
              <div className="text-sm font-medium text-slate-400 mb-1">Filtered Servers</div>
              <div className="text-4xl font-bold text-white mb-1">{filteredServers.length} VMs</div>
          </div>
          <div>
              <div className="text-sm font-medium text-slate-400 mb-1">Total CPUs Allocation</div>
              <div className="text-4xl font-bold text-white mb-1">{totalCpus} vCPUs</div>
          </div>
          <div>
              <div className="text-sm font-medium text-slate-400 mb-1">Avg. CPU Utilization</div>
              <div className="text-4xl font-bold text-white mb-1">{avgCpu.toFixed(1)}%</div>
          </div>
          <div>
              <div className="text-sm font-medium text-slate-400 mb-1">Avg. RAM Utilization</div>
              <div className="text-4xl font-bold text-white mb-1">{avgRam.toFixed(1)}%</div>
          </div>
      </div>
      
      <div className="h-px bg-white/10 w-full mb-8"></div>

      {/* TABLE VIEW */}
      <h3 className="text-2xl font-bold text-white mb-4">Inventory Details</h3>
      <div className="bg-[#131826] rounded-xl border border-white/10 overflow-hidden mb-10 shadow-lg">
          <div className="overflow-x-auto max-h-[400px] custom-scrollbar">
              <table className="w-full text-xs text-left">
                  <thead className="text-slate-400 bg-slate-900 border-b border-white/10 sticky top-0 z-10">
                      <tr>
                          <th className="p-3 font-semibold">server_id</th>
                          <th className="p-3 font-semibold">name</th>
                          <th className="p-3 font-semibold">vcpu</th>
                          <th className="p-3 font-semibold">ram_gb</th>
                          <th className="p-3 font-semibold">disk_gb</th>
                          <th className="p-3 font-semibold">os</th>
                          <th className="p-3 font-semibold">ip_address</th>
                          <th className="p-3 font-semibold">power_state</th>
                          <th className="p-3 font-semibold">workload_type</th>
                          <th className="p-3 font-semibold">environment</th>
                      </tr>
                  </thead>
                  <tbody className="text-slate-300 divide-y divide-white/5 bg-[#0f141f]">
                      {filteredServers.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE).map((s, i) => (
                          <tr key={i} className="hover:bg-white/5">
                              <td className="p-3 text-slate-500">{s.server_id}</td>
                              <td className="p-3 font-medium text-indigo-300">{s.name}</td>
                              <td className="p-3">{s.vcpu}</td>
                              <td className="p-3">{s.ram_gb}</td>
                              <td className="p-3">{s.disk_gb}</td>
                              <td className="p-3">{s.os}</td>
                              <td className="p-3 text-slate-400">{s.ip_address}</td>
                              <td className="p-3">{s.power_state}</td>
                              <td className="p-3">{s.workload_type}</td>
                              <td className="p-3">{s.environment}</td>
                          </tr>
                      ))}
                      {filteredServers.length === 0 && (
                          <tr><td colSpan="10" className="p-4 text-center text-slate-400">No servers match filters.</td></tr>
                      )}
                  </tbody>
              </table>
              {/* Pagination */}
              {filteredServers.length > PAGE_SIZE && (
                <div className="flex items-center justify-between p-4 border-t border-white/5 bg-slate-900/30">
                  <span className="text-xs text-slate-400">Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filteredServers.length)} of {filteredServers.length.toLocaleString()} servers</span>
                  <div className="flex gap-2">
                    <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="px-3 py-1.5 text-xs font-bold bg-slate-800 border border-white/10 rounded-lg text-slate-300 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">← Prev</button>
                    <span className="px-3 py-1.5 text-xs font-bold text-slate-400">Page {page + 1} / {Math.ceil(filteredServers.length / PAGE_SIZE)}</span>
                    <button disabled={(page + 1) * PAGE_SIZE >= filteredServers.length} onClick={() => setPage(p => p + 1)} className="px-3 py-1.5 text-xs font-bold bg-slate-800 border border-white/10 rounded-lg text-slate-300 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">Next →</button>
                  </div>
                </div>
              )}
          </div>
      </div>
      
      {/* DISTRIBUTION CHARTS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
          <div className="bg-[#131826] rounded-xl p-6 border border-white/10 shadow-lg">
              <h3 className="text-xl font-bold text-white mb-2">OS Distribution</h3>
              <p className="text-xs text-slate-400 mb-6">Operating System Share</p>
              <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                          <Pie 
                            data={osData} 
                            cx="50%" cy="50%" 
                            innerRadius={60} outerRadius={110} 
                            paddingAngle={2} dataKey="value"
                          >
                              {osData.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={OS_COLORS[index % OS_COLORS.length]} />
                              ))}
                          </Pie>
                          <RechartsTooltip 
                            contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff'}}
                            itemStyle={{color: '#fff'}}
                          />
                      </PieChart>
                  </ResponsiveContainer>
              </div>
          </div>
          
          <div className="bg-[#131826] rounded-xl p-6 border border-white/10 shadow-lg">
              <h3 className="text-xl font-bold text-white mb-2">Workload Types</h3>
              <p className="text-xs text-slate-400 mb-6">VM Categorization</p>
              <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={workloadData} margin={{ top: 0, right: 0, left: -20, bottom: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                          <XAxis dataKey="name" stroke="#64748b" tick={{fontSize: 11}} axisLine={false} tickLine={false} dy={10} />
                          <YAxis stroke="#64748b" tick={{fontSize: 11}} axisLine={false} tickLine={false} />
                          <RechartsTooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff'}} />
                          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                              {workloadData.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={WORKLOAD_COLORS[index % WORKLOAD_COLORS.length]} />
                              ))}
                          </Bar>
                      </BarChart>
                  </ResponsiveContainer>
              </div>
          </div>
      </div>

      {/* ADVANCED CHARTS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-[#131826] rounded-xl p-6 border border-white/10 shadow-lg">
              <h3 className="text-xl font-bold text-white mb-4">CPU & RAM Utilization Heatmap</h3>
              <div className="h-[300px] overflow-x-auto custom-scrollbar flex">
                  {/* CSS Grid Heatmap */}
                  <div className="min-w-full flex flex-col justify-center pb-12">
                      <div className="flex mb-1">
                          <div className="w-12 text-xs text-slate-400 flex items-center justify-end pr-2">RAM %</div>
                          <div className="flex-1 flex gap-1">
                              {activeVMs.map((s, i) => (
                                  <div key={`ram-${i}`} className="flex-1 h-8 rounded-sm relative group" style={{backgroundColor: getHeatmapColor(s.ram_utilization_avg)}}>
                                      <div className="absolute opacity-0 group-hover:opacity-100 bg-black text-xs p-2 rounded -top-10 left-1/2 -translate-x-1/2 z-20 whitespace-nowrap pointer-events-none">
                                          {s.name}: {s.ram_utilization_avg}% RAM
                                      </div>
                                  </div>
                              ))}
                          </div>
                      </div>
                      <div className="flex relative">
                          <div className="w-12 text-xs text-slate-400 flex items-center justify-end pr-2">CPU %</div>
                          <div className="flex-1 flex gap-1">
                              {activeVMs.map((s, i) => (
                                  <div key={`cpu-${i}`} className="flex-1 h-8 rounded-sm relative group" style={{backgroundColor: getHeatmapColor(s.cpu_utilization_avg)}}>
                                       <div className="absolute opacity-0 group-hover:opacity-100 bg-black text-xs p-2 rounded -bottom-10 left-1/2 -translate-x-1/2 z-20 whitespace-nowrap pointer-events-none">
                                          {s.name}: {s.cpu_utilization_avg}% CPU
                                      </div>
                                      {/* VM Name label (rotated) */}
                                      <div className="absolute top-10 left-1/2 -translate-x-1/2 origin-top-left -rotate-45 text-[8px] text-slate-400 whitespace-nowrap w-32 overflow-hidden text-ellipsis">
                                          {s.name}
                                      </div>
                                  </div>
                              ))}
                          </div>
                      </div>
                      {activeVMs.length === 0 && <div className="text-center text-slate-500 mt-10">No active VMs for Heatmap</div>}
                  </div>
              </div>
          </div>

          <div className="bg-[#131826] rounded-xl p-6 border border-white/10 shadow-lg">
              <h3 className="text-xl font-bold text-white mb-2">Resource Allocation Treemap</h3>
              <p className="text-xs text-slate-400 mb-4">vCPU Allocation by Workload</p>
              <div className="h-[280px]">
                  {treemapData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                          <Treemap
                              data={treemapData}
                              dataKey="size"
                              aspectRatio={4 / 3}
                              stroke="#0b0f19"
                              fill="#4f46e5"
                          >
                              <RechartsTooltip 
                                contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff'}}
                                itemStyle={{color: '#fff'}}
                              />
                          </Treemap>
                      </ResponsiveContainer>
                  ) : (
                      <div className="h-full flex items-center justify-center text-slate-500">No data for Treemap</div>
                  )}
              </div>
          </div>
      </div>

    </main>
  );
}
