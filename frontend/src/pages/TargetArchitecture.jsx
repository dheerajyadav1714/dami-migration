import React, { useEffect, useState, useMemo } from 'react';
import api from '../lib/api';
import axios from 'axios';
import { Network, ArrowRight, Cloud, Server, Database, Cpu, Bot, Loader2 } from 'lucide-react';

const GCP_MAPPINGS = {
  'LB': { gcp: 'Cloud Load Balancing', icon: '⚖️', type: 'Networking' },
  'WEB': { gcp: 'Compute Engine (Auto-Scaling)', icon: '🖥️', type: 'Compute' },
  'APP': { gcp: 'Google Kubernetes Engine', icon: '☸️', type: 'Compute' },
  'DB': { gcp: 'Cloud SQL / Bare Metal', icon: '🗄️', type: 'Database' },
  'CACHE': { gcp: 'Memorystore for Redis', icon: '⚡', type: 'Cache' },
  'QUEUE': { gcp: 'Cloud Pub/Sub', icon: '📨', type: 'Messaging' },
  'INFRA': { gcp: 'Cloud Identity', icon: '🔑', type: 'Identity' },
  'LEGACY': { gcp: 'Retire', icon: '🗑️', type: 'Decommission' },
};

const CLOUD_PROVIDERS = ['Google Cloud Platform', 'Multi-Cloud (GCP Primary)'];

const MERMAID_DIAGRAM = `graph TD
    subgraph On-Premises["🏢 On-Premises Datacenter"]
        LB["⚖️ LB-NGINX-01<br/>Load Balancer"]
        WEB1["🖥️ WEBAPP-PROD-01<br/>Web Server"]
        WEB2["🖥️ WEBAPP-PROD-02<br/>Web Server"]
        APP["📱 APP-PAYMENT-01<br/>Payment Engine"]
        DB["🗄️ DB-ORACLE-01<br/>Oracle Database"]
        CACHE["⚡ CACHE-REDIS-01<br/>Redis Cache"]
        QUEUE["📨 QUEUE-RABBIT-01<br/>RabbitMQ"]
        LDAP["🔑 INFRA-LDAP-01<br/>LDAP Server"]
    end
    
    subgraph GCP["☁️ Google Cloud Platform"]
        GLB["⚖️ Cloud Load Balancing"]
        GCE1["🖥️ Compute Engine<br/>Auto-Scaling MIG"]
        GKE["☸️ GKE Cluster<br/>Payment Microservices"]
        CSQL["🗄️ Cloud SQL<br/>PostgreSQL"]
        BMS["🗄️ Bare Metal Solution<br/>Oracle Compatible"]
        MEM["⚡ Memorystore<br/>Redis"]
        PUBSUB["📨 Cloud Pub/Sub"]
        CID["🔑 Cloud Identity"]
    end
    
    LB -.->|Rehost| GLB
    WEB1 -.->|Rehost| GCE1
    WEB2 -.->|Rehost| GCE1
    APP -.->|Refactor| GKE
    DB -.->|Relocate| BMS
    CACHE -.->|Replatform| MEM
    QUEUE -.->|Replatform| PUBSUB
    LDAP -.->|Repurchase| CID`;

export default function TargetArchitecture() {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState('Google Cloud Platform');
  const [aiArch, setAiArch] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    api.get('/api/inventory/servers')
      .then(res => setServers(res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const mappings = useMemo(() => {
    return servers.map(s => {
      const mapping = GCP_MAPPINGS[s.workload_type] || { gcp: 'Compute Engine', icon: '🖥️', type: 'Compute' };
      return { ...s, ...mapping };
    });
  }, [servers]);

  const gcpServiceCounts = useMemo(() => {
    const counts = {};
    mappings.forEach(m => { counts[m.gcp] = (counts[m.gcp] || 0) + 1; });
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [mappings]);

  const generateAiArch = async () => {
    setAiLoading(true);
    try {
      const serverSummary = mappings.slice(0, 10).map(m => `${m.name} (${m.workload_type}) → ${m.gcp}`).join(', ');
      const res = await api.post('/api/chat', { prompt: `Generate a detailed GCP target architecture recommendation for migrating these on-premises servers: ${serverSummary}. Include: VPC design, network topology, security zones, managed services selection rationale, and high-availability configuration. Format as a professional architecture document.` });
      setAiArch(res.data?.reply || 'Failed to generate architecture.');
    } catch {
      setAiArch('Failed to generate. Ensure backend is running.');
    } finally {
      setAiLoading(false);
    }
  };

  if (loading) return <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full"><div className="text-indigo-400 text-xl font-bold animate-pulse">Loading Architecture...</div></main>;

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Target Architecture</h1>
            <p className="text-slate-400 font-medium">AI-generated GCP service mappings and architecture topology for your migration.</p>
          </div>
          <div className="flex gap-3 items-center">
            <select value={selectedProvider} onChange={e => setSelectedProvider(e.target.value)} className="bg-[#131826] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white">
              {CLOUD_PROVIDERS.map(p => <option key={p}>{p}</option>)}
            </select>
          </div>
        </div>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* GCP Services Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {gcpServiceCounts.map(([service, count], i) => (
          <div key={i} className="bg-[#131826] rounded-xl p-4 border border-white/[0.05]">
            <div className="text-xs text-slate-400 mb-1">{service}</div>
            <div className="text-2xl font-bold text-white">{count} <span className="text-sm text-slate-400">servers</span></div>
          </div>
        ))}
      </div>

      {/* Visual Topology Diagram (Mermaid-style) */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg mb-8">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">🗺️ Visual Topology Diagram</h3>
        <div className="relative bg-slate-900/50 rounded-xl border border-white/5 p-8 overflow-x-auto">
          <div className="flex items-center justify-center gap-16 min-w-[600px]">
            {/* On-Prem Side */}
            <div className="flex flex-col gap-3">
              <div className="text-sm font-bold text-red-400 mb-2 text-center">🏢 On-Premises</div>
              {mappings.slice(0, 8).map((m, i) => (
                <div key={i} className="bg-red-500/5 border border-red-500/20 rounded-lg px-4 py-2 text-xs text-slate-300 flex items-center gap-2 whitespace-nowrap">
                  <Server className="w-3 h-3 text-red-400" /> {m.name}
                </div>
              ))}
            </div>
            {/* Arrow */}
            <div className="flex flex-col items-center gap-2">
              <div className="text-xs text-indigo-400 font-bold">D.A.M.I.</div>
              <div className="flex flex-col gap-1">
                {['Rehost', 'Replatform', 'Refactor', 'Relocate'].map((s, i) => (
                  <div key={i} className="flex items-center gap-1">
                    <div className="w-8 h-px bg-indigo-400" />
                    <span className="text-[9px] text-indigo-300">{s}</span>
                    <ArrowRight className="w-3 h-3 text-indigo-400" />
                  </div>
                ))}
              </div>
            </div>
            {/* GCP Side */}
            <div className="flex flex-col gap-3">
              <div className="text-sm font-bold text-emerald-400 mb-2 text-center">☁️ Google Cloud</div>
              {gcpServiceCounts.map(([service], i) => (
                <div key={i} className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg px-4 py-2 text-xs text-slate-300 flex items-center gap-2 whitespace-nowrap">
                  <Cloud className="w-3 h-3 text-emerald-400" /> {service}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* AI-Generated Architecture */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white flex items-center gap-2"><Bot className="w-5 h-5 text-indigo-400" /> 🤖 AI-Generated Architecture (Gemini)</h3>
          <button onClick={generateAiArch} disabled={aiLoading} className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-5 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-colors">
            {aiLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</> : <><Cpu className="w-4 h-4" /> Generate</>}
          </button>
        </div>
        {aiArch ? (
          <pre className="bg-slate-900/50 rounded-xl p-5 text-xs font-mono text-slate-300 overflow-x-auto border border-white/5 max-h-[400px] custom-scrollbar whitespace-pre-wrap">{aiArch}</pre>
        ) : (
          <div className="bg-slate-900/30 rounded-xl p-8 text-center border border-white/5">
            <Bot className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <div className="text-sm text-slate-400">Click "Generate" to create an AI-powered architecture recommendation using Gemini.</div>
          </div>
        )}
      </div>

      {/* Component Mapping Table */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg mb-8">
        <h3 className="text-xl font-bold text-white mb-4">🔍 Component Mapping Table</h3>
        <div className="overflow-x-auto max-h-[500px] custom-scrollbar">
          <table className="w-full text-sm text-left">
            <thead className="text-slate-400 bg-slate-900 border-b border-white/10 sticky top-0 z-10">
              <tr>
                <th className="p-3">Source VM</th><th className="p-3">Workload</th><th className="p-3">OS</th>
                <th className="p-3 text-center">→</th><th className="p-3">GCP Target</th><th className="p-3">Type</th>
              </tr>
            </thead>
            <tbody className="text-slate-300 divide-y divide-white/5 bg-[#0f141f]">
              {mappings.slice(0, 100).map((m, i) => (
                <tr key={i} className="hover:bg-white/5">
                  <td className="p-3 font-medium text-indigo-300 flex items-center gap-2"><Server className="w-4 h-4 text-slate-500" /> {m.name}</td>
                  <td className="p-3"><span className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded-full text-xs">{m.workload_type}</span></td>
                  <td className="p-3 text-xs text-slate-400">{m.os}</td>
                  <td className="p-3 text-center"><ArrowRight className="w-4 h-4 text-indigo-400 mx-auto" /></td>
                  <td className="p-3 font-medium text-emerald-300 flex items-center gap-2"><span>{m.icon}</span> {m.gcp}</td>
                  <td className="p-3 text-xs text-slate-400">{m.type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Eraser.io Style Mermaid */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg">
        <h3 className="text-xl font-bold text-white mb-4">🎨 Eraser.io Style (Mermaid Diagram Code)</h3>
        <p className="text-xs text-slate-400 mb-4">Copy this Mermaid code into <a href="https://eraser.io" target="_blank" rel="noreferrer" className="text-indigo-400 underline">eraser.io</a> or <a href="https://mermaid.live" target="_blank" rel="noreferrer" className="text-indigo-400 underline">mermaid.live</a> to render the architecture diagram.</p>
        <pre className="bg-slate-900/50 rounded-xl p-5 text-xs font-mono text-slate-300 overflow-x-auto border border-white/5 max-h-[300px] custom-scrollbar">{MERMAID_DIAGRAM}</pre>
      </div>
    </main>
  );
}
