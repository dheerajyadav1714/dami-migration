import React, { useState, useEffect, useMemo } from 'react';
import api from '../lib/api';
import axios from 'axios';
import { 
  Network, Search, Filter, Server, Database, Globe2
} from 'lucide-react';

const TYPE_COLORS = {
  database: '#f59e0b',
  cache: '#10b981',
  http: '#3b82f6',
  messaging: '#8b5cf6',
  authentication: '#ec4899',
  storage: '#14b8a6'
};

const SENSITIVITY_BADGE = {
  critical: 'bg-red-500/10 text-red-400',
  high: 'bg-orange-500/10 text-orange-400',
  medium: 'bg-yellow-500/10 text-yellow-400',
  low: 'bg-green-500/10 text-green-400'
};

export default function DependencyMap() {
  const [deps, setDeps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');

  useEffect(() => {
    api.get('/api/dependencies')
      .then(res => setDeps(res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const depTypes = ['All', ...Array.from(new Set(deps.map(d => d.dependency_type))).sort()];

  const filtered = useMemo(() => {
    return deps.filter(d => {
      const matchType = typeFilter === 'All' || d.dependency_type === typeFilter;
      const matchSearch = searchQuery === '' ||
        d.source_server?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        d.target_server?.toLowerCase().includes(searchQuery.toLowerCase());
      return matchType && matchSearch;
    });
  }, [deps, typeFilter, searchQuery]);

  // Build unique nodes from edges
  const nodes = useMemo(() => {
    const nodeSet = new Set();
    deps.forEach(d => { nodeSet.add(d.source_server); nodeSet.add(d.target_server); });
    return Array.from(nodeSet);
  }, [deps]);

  // Connection counts per node
  const nodeCounts = useMemo(() => {
    const counts = {};
    deps.forEach(d => {
      counts[d.source_server] = (counts[d.source_server] || 0) + 1;
      counts[d.target_server] = (counts[d.target_server] || 0) + 1;
    });
    return counts;
  }, [deps]);

  if (loading) {
    return (
      <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full">
        <div className="text-indigo-400 text-xl font-bold animate-pulse">Mapping Dependencies...</div>
      </main>
    );
  }

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">
          Application Dependency Map
        </h1>
        <p className="text-slate-400 font-medium">
          Visualize how servers communicate — critical for planning migration wave sequencing and avoiding cutover failures.
        </p>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Total Nodes</div>
          <div className="text-3xl font-bold text-white">{nodes.length}</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Total Edges</div>
          <div className="text-3xl font-bold text-white">{deps.length}</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Critical Latency</div>
          <div className="text-3xl font-bold text-red-400">{deps.filter(d => d.latency_sensitivity === 'critical').length}</div>
        </div>
        <div className="bg-[#131826] rounded-xl p-5 border border-white/[0.05]">
          <div className="text-sm text-slate-400 mb-1">Dependency Types</div>
          <div className="text-3xl font-bold text-white">{depTypes.length - 1}</div>
        </div>
      </div>

      {/* VISUAL GRAPH (CSS-based Force Layout) */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg mb-8">
        <h3 className="text-xl font-bold text-white mb-4">Network Topology</h3>
        <div className="relative h-[350px] bg-slate-900/50 rounded-xl border border-white/5 overflow-hidden">
          {/* Render nodes in a circle layout */}
          {nodes.map((node, i) => {
            const angle = (2 * Math.PI * i) / nodes.length;
            const cx = 50 + 35 * Math.cos(angle);
            const cy = 50 + 35 * Math.sin(angle);
            const size = Math.min(60, 30 + (nodeCounts[node] || 0) * 5);
            return (
              <div key={node} className="absolute group" style={{ left: `${cx}%`, top: `${cy}%`, transform: 'translate(-50%, -50%)' }}>
                <div className="w-12 h-12 rounded-full bg-indigo-600/30 border-2 border-indigo-400/50 flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.3)] hover:shadow-[0_0_25px_rgba(99,102,241,0.6)] transition-all cursor-pointer"
                  style={{ width: `${size}px`, height: `${size}px` }}>
                  <Server className="w-4 h-4 text-indigo-300" />
                </div>
                <div className="absolute top-full mt-1 left-1/2 -translate-x-1/2 text-[9px] text-slate-300 whitespace-nowrap font-medium bg-slate-900/80 px-1.5 py-0.5 rounded">
                  {node}
                </div>
                <div className="absolute opacity-0 group-hover:opacity-100 bottom-full mb-2 left-1/2 -translate-x-1/2 bg-black text-xs p-2 rounded whitespace-nowrap z-20 pointer-events-none">
                  {nodeCounts[node] || 0} connections
                </div>
              </div>
            );
          })}
          {/* SVG edges */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
            {filtered.map((d, i) => {
              const si = nodes.indexOf(d.source_server);
              const ti = nodes.indexOf(d.target_server);
              if (si === -1 || ti === -1) return null;
              const sAngle = (2 * Math.PI * si) / nodes.length;
              const tAngle = (2 * Math.PI * ti) / nodes.length;
              const sx = 50 + 35 * Math.cos(sAngle);
              const sy = 50 + 35 * Math.sin(sAngle);
              const tx = 50 + 35 * Math.cos(tAngle);
              const ty = 50 + 35 * Math.sin(tAngle);
              const color = TYPE_COLORS[d.dependency_type] || '#6366f1';
              return <line key={i} x1={sx} y1={sy} x2={tx} y2={ty} stroke={color} strokeWidth="0.3" strokeOpacity="0.6" />;
            })}
          </svg>
        </div>
        <div className="flex flex-wrap gap-3 mt-4">
          {Object.entries(TYPE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5 text-xs text-slate-400">
              <div className="w-3 h-0.5 rounded" style={{ backgroundColor: color }} />
              <span className="capitalize">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* FILTERS + TABLE */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white">Dependency Register</h3>
          <div className="flex gap-3">
            <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="bg-slate-900 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white">
              {depTypes.map(t => <option key={t}>{t}</option>)}
            </select>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
              <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search..." className="bg-slate-900 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white w-48" />
            </div>
          </div>
        </div>
        <div className="overflow-x-auto max-h-[400px] custom-scrollbar">
          <table className="w-full text-xs text-left">
            <thead className="text-slate-400 bg-slate-900 border-b border-white/10 sticky top-0 z-10">
              <tr>
                <th className="p-3 font-semibold">Source Server</th>
                <th className="p-3 font-semibold">→</th>
                <th className="p-3 font-semibold">Target Server</th>
                <th className="p-3 font-semibold">Type</th>
                <th className="p-3 font-semibold">Protocol</th>
                <th className="p-3 font-semibold">Latency Sensitivity</th>
              </tr>
            </thead>
            <tbody className="text-slate-300 divide-y divide-white/5 bg-[#0f141f]">
              {filtered.map((d, i) => (
                <tr key={i} className="hover:bg-white/5">
                  <td className="p-3 font-medium text-indigo-300">{d.source_server}</td>
                  <td className="p-3 text-slate-500">→</td>
                  <td className="p-3 font-medium text-purple-300">{d.target_server}</td>
                  <td className="p-3">
                    <span className="inline-flex items-center gap-1.5 capitalize">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: TYPE_COLORS[d.dependency_type] || '#6366f1' }} />
                      {d.dependency_type}
                    </span>
                  </td>
                  <td className="p-3 font-mono text-slate-400">{d.protocol}</td>
                  <td className="p-3">
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${SENSITIVITY_BADGE[d.latency_sensitivity] || 'bg-slate-500/10 text-slate-400'}`}>
                      {d.latency_sensitivity}
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan="6" className="p-4 text-center text-slate-400">No dependencies match filters.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
