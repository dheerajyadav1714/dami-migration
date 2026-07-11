import React, { useEffect, useState, useMemo } from 'react';
import api from '../lib/api';
import { Network, ArrowRight, Cloud, Server, Database, Cpu, Bot, Loader2, Copy, Check, ChevronDown, ChevronRight, DollarSign, Shield, Layers, Zap, MapPin, Maximize2, ExternalLink, X } from 'lucide-react';
import Mermaid from '../components/Mermaid';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const CLOUD_PROVIDERS = [
  { value: 'Google Cloud Platform', label: 'Google Cloud', icon: '☁️', color: 'from-blue-500 to-emerald-500' },
  { value: 'AWS', label: 'Amazon Web Services', icon: '🟧', color: 'from-orange-500 to-yellow-500' },
  { value: 'Microsoft Azure', label: 'Microsoft Azure', icon: '🔵', color: 'from-blue-600 to-cyan-500' },
];

const SERVICE_ICONS = {
  'Compute Engine': { icon: '🖥️', color: 'bg-blue-500/10 border-blue-500/20 text-blue-400' },
  'Amazon EC2': { icon: '🖥️', color: 'bg-orange-500/10 border-orange-500/20 text-orange-400' },
  'Azure Virtual Machines': { icon: '🖥️', color: 'bg-sky-500/10 border-sky-500/20 text-sky-400' },
  'GKE Autopilot': { icon: '☸️', color: 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' },
  'Amazon EKS': { icon: '☸️', color: 'bg-orange-500/10 border-orange-500/20 text-orange-400' },
  'Azure Kubernetes': { icon: '☸️', color: 'bg-sky-500/10 border-sky-500/20 text-sky-400' },
  'Cloud SQL': { icon: '🗄️', color: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' },
  'Amazon RDS': { icon: '🗄️', color: 'bg-orange-500/10 border-orange-500/20 text-orange-400' },
  'Azure Database': { icon: '🗄️', color: 'bg-sky-500/10 border-sky-500/20 text-sky-400' },
  'Cloud Load Balancing': { icon: '⚖️', color: 'bg-purple-500/10 border-purple-500/20 text-purple-400' },
  'Elastic Load': { icon: '⚖️', color: 'bg-orange-500/10 border-orange-500/20 text-orange-400' },
  'Azure Load': { icon: '⚖️', color: 'bg-sky-500/10 border-sky-500/20 text-sky-400' },
  'Memorystore': { icon: '⚡', color: 'bg-amber-500/10 border-amber-500/20 text-amber-400' },
  'ElastiCache': { icon: '⚡', color: 'bg-orange-500/10 border-orange-500/20 text-orange-400' },
  'Azure Cache': { icon: '⚡', color: 'bg-sky-500/10 border-sky-500/20 text-sky-400' },
  'Pub/Sub': { icon: '📨', color: 'bg-pink-500/10 border-pink-500/20 text-pink-400' },
  'Amazon SNS': { icon: '📨', color: 'bg-orange-500/10 border-orange-500/20 text-orange-400' },
  'Azure Service Bus': { icon: '📨', color: 'bg-sky-500/10 border-sky-500/20 text-sky-400' },
  'Bare Metal': { icon: '🏗️', color: 'bg-red-500/10 border-red-500/20 text-red-400' },
  'Managed Service': { icon: '🔑', color: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400' },
  'AWS Directory': { icon: '🔑', color: 'bg-orange-500/10 border-orange-500/20 text-orange-400' },
  'Azure Active Directory': { icon: '🔑', color: 'bg-sky-500/10 border-sky-500/20 text-sky-400' },
  'Retire': { icon: '🗑️', color: 'bg-slate-500/10 border-slate-500/20 text-slate-400' },
};

const getServiceStyle = (name) => {
  if (!name) return { icon: '☁️', color: 'bg-slate-500/10 border-slate-500/20 text-slate-400' };
  for (const [key, val] of Object.entries(SERVICE_ICONS)) {
    if (name.includes(key)) return val;
  }
  return { icon: '☁️', color: 'bg-slate-500/10 border-slate-500/20 text-slate-400' };
};

const STRATEGY_COLORS = {
  'rehost': 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  'replatform': 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  'refactor': 'bg-purple-500/15 text-purple-400 border-purple-500/30',
  'retire': 'bg-red-500/15 text-red-400 border-red-500/30',
  'relocate': 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  'repurchase': 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
};

export default function TargetArchitecture() {
  const [archData, setArchData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState('Google Cloud Platform');
  const [aiArch, setAiArch] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('topology');
  const [copiedMermaid, setCopiedMermaid] = useState(false);
  const [expandedRows, setExpandedRows] = useState({});
  const [filterService, setFilterService] = useState('All');
  const [aiSubTab, setAiSubTab] = useState('diagram');
  const [isFullscreen, setIsFullscreen] = useState(false);

  const getMermaidLiveUrl = (code) => {
    if (!code) return '#';
    try {
      const state = { code, mermaid: { theme: 'dark' } };
      // Unicode safe base64 encoding
      const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(state))));
      return `https://mermaid.live/edit#base64:${encoded}`;
    } catch (e) {
      return 'https://mermaid.live';
    }
  };

  // Fetch architecture data — re-fetches when cloud provider changes
  useEffect(() => {
    setLoading(true);
    api.get(`/api/target-architecture?cloud_provider=${encodeURIComponent(selectedProvider)}`)
      .then(res => setArchData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedProvider]);

  // Reset AI output and filter when provider changes
  useEffect(() => {
    setAiArch(null);
    setFilterService('All');
  }, [selectedProvider]);

  const { mermaidCode, markdownText } = useMemo(() => {
    if (!aiArch) return { mermaidCode: null, markdownText: null };
    const mermaidMatch = aiArch.match(/```+mermaid\s+([\s\S]*?)```+/i);
    const code = mermaidMatch ? mermaidMatch[1].trim() : null;
    const text = aiArch.replace(/```+mermaid\s+[\s\S]*?```+/i, '').trim();
    return { mermaidCode: code, markdownText: text };
  }, [aiArch]);

  const generateAiArch = async () => {
    setAiLoading(true);
    setAiArch(null);
    try {
      const res = await api.post('/api/target-architecture/generate', { prompt: selectedProvider });
      setAiArch(res.data?.reply || 'Failed to generate architecture.');
    } catch {
      setAiArch('Failed to generate. Please try again.');
    } finally {
      setAiLoading(false);
    }
  };

  const copyMermaid = () => {
    if (archData?.mermaid_code) {
      navigator.clipboard.writeText(archData.mermaid_code);
      setCopiedMermaid(true);
      setTimeout(() => setCopiedMermaid(false), 2000);
    }
  };

  const toggleRow = (i) => setExpandedRows(prev => ({ ...prev, [i]: !prev[i] }));

  const filteredMappings = useMemo(() => {
    if (!archData?.mappings) return [];
    if (filterService === 'All') return archData.mappings;
    return archData.mappings.filter(m => m.target_service === filterService);
  }, [archData, filterService]);

  const currentProvider = CLOUD_PROVIDERS.find(p => p.value === selectedProvider) || CLOUD_PROVIDERS[0];

  if (loading) return <main className="flex-1 bg-[#0b0f19] flex items-center justify-center h-full"><div className="text-indigo-400 text-xl font-bold animate-pulse">Loading Architecture...</div></main>;

  const tabs = [
    { id: 'topology', label: '🗺️ Visual Topology' },
    { id: 'ai', label: '🤖 AI Architecture' },
    { id: 'mapping', label: '🔍 Component Mapping' },
  ];

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      {/* Header */}
      <header className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Target Architecture & Mapping</h1>
            <p className="text-slate-400 font-medium">AI-powered {currentProvider.label} service mappings from {archData?.total_mapped || 0} analyzed workloads in BigQuery.</p>
          </div>
          <div className="flex gap-3 items-center">
            <select 
              value={selectedProvider} 
              onChange={e => setSelectedProvider(e.target.value)} 
              className="bg-[#131826] border border-white/10 rounded-xl px-5 py-3 text-sm text-white font-semibold cursor-pointer hover:border-indigo-500/50 transition-colors"
            >
              {CLOUD_PROVIDERS.map(p => <option key={p.value} value={p.value}>{p.icon} {p.label}</option>)}
            </select>
          </div>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gradient-to-br from-indigo-500/10 to-purple-500/10 rounded-xl p-5 border border-indigo-500/20">
          <div className="flex items-center gap-2 mb-2">
            <Server className="w-4 h-4 text-indigo-400" />
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Mapped Workloads</span>
          </div>
          <div className="text-3xl font-black text-white">{archData?.total_mapped || 0}</div>
        </div>
        <div className="bg-gradient-to-br from-emerald-500/10 to-teal-500/10 rounded-xl p-5 border border-emerald-500/20">
          <div className="flex items-center gap-2 mb-2">
            <Cloud className="w-4 h-4 text-emerald-400" />
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Target Services</span>
          </div>
          <div className="text-3xl font-black text-white">{archData?.service_summary?.length || 0}</div>
        </div>
        <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-xl p-5 border border-amber-500/20">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-4 h-4 text-amber-400" />
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Est. Monthly Cost</span>
          </div>
          <div className="text-3xl font-black text-white">${(archData?.total_cost || 0).toLocaleString()}</div>
        </div>
        <div className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 rounded-xl p-5 border border-cyan-500/20">
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="w-4 h-4 text-cyan-400" />
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Target Region</span>
          </div>
          <div className="text-xl font-black text-white mt-1">{archData?.target_region || 'us-central1'}</div>
        </div>
      </div>

      {/* Service Distribution */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-8">
        {archData?.service_summary?.map((svc, i) => {
          const style = getServiceStyle(svc.target_service);
          return (
            <div key={i} className={`${style.color} rounded-xl p-4 border cursor-pointer hover:scale-[1.02] transition-transform`}
              onClick={() => { setFilterService(svc.target_service); setActiveTab('mapping'); }}>
              <div className="text-lg mb-1">{style.icon}</div>
              <div className="text-xs font-semibold text-slate-300 mb-1 truncate" title={svc.target_service}>{svc.target_service}</div>
              <div className="text-xl font-black text-white">{svc.server_count}</div>
              <div className="text-[10px] text-slate-400 mt-1">${svc.total_monthly_cost?.toLocaleString()}/mo</div>
            </div>
          );
        })}
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 bg-[#131826] rounded-xl p-1.5 border border-white/[0.05] w-fit">
        {tabs.map(tab => (
          <button key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-2.5 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${
              activeTab === tab.id 
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' 
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'topology' && (
        <div className="bg-[#131826] rounded-2xl p-8 border border-white/[0.05] shadow-xl">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">Architecture Topology ({currentProvider.label})</h3>
              <p className="text-sm text-slate-400 mt-1">Data-driven from {archData?.total_mapped || 0} mapped workloads in BigQuery</p>
            </div>
            <button onClick={copyMermaid} className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg text-xs font-bold text-slate-300 transition-colors border border-white/10">
              {copiedMermaid ? <><Check className="w-4 h-4 text-emerald-400" /> Copied!</> : <><Copy className="w-4 h-4" /> Copy Mermaid</>}
            </button>
          </div>
          
          {/* Professional Topology */}
          <div className="relative bg-gradient-to-br from-slate-900/80 to-slate-900/40 rounded-2xl border border-white/5 p-10 overflow-x-auto">
            <div className="flex items-stretch justify-between gap-6 min-w-[900px]">
              
              {/* Source: On-Premises */}
              <div className="flex-1 max-w-[280px]">
                <div className="text-center mb-4">
                  <div className="inline-flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-full px-4 py-1.5">
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                    <span className="text-xs font-bold text-red-400 uppercase tracking-wider">On-Premises VMware</span>
                  </div>
                </div>
                <div className="space-y-2">
                  {archData?.mappings && (() => {
                    const groups = {};
                    archData.mappings.forEach(m => {
                      const wt = m.workload_type || 'APP';
                      if (!groups[wt]) groups[wt] = 0;
                      groups[wt]++;
                    });
                    return Object.entries(groups).sort((a, b) => b[1] - a[1]).map(([wt, count], i) => {
                      const wtIcons = { APP: '📱', WEB: '🖥️', DB: '🗄️', CACHE: '⚡', LB: '⚖️', QUEUE: '📨', INFRA: '🔑', LEGACY: '🗑️' };
                      return (
                        <div key={i} className="bg-red-500/5 border border-red-500/15 rounded-xl px-4 py-3 flex items-center justify-between group hover:border-red-500/30 transition-colors">
                          <div className="flex items-center gap-3">
                            <span className="text-sm">{wtIcons[wt] || '📦'}</span>
                            <div>
                              <div className="text-xs font-bold text-slate-300">{wt}</div>
                              <div className="text-[10px] text-slate-500">VMware VMs</div>
                            </div>
                          </div>
                          <div className="bg-red-500/20 rounded-full px-2.5 py-0.5 text-[10px] font-bold text-red-400">{count}</div>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>

              {/* Center: DAMI AI Engine */}
              <div className="flex flex-col items-center justify-center px-4">
                <div className="bg-gradient-to-b from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 rounded-2xl p-5 text-center mb-4">
                  <div className="text-2xl mb-2">🤖</div>
                  <div className="text-xs font-black text-indigo-400 uppercase tracking-widest">D.A.M.I.</div>
                  <div className="text-[10px] text-slate-500 mt-1">AI Engine</div>
                </div>
                <div className="space-y-3">
                  {[
                    { label: 'Rehost', color: 'bg-blue-500', line: 'border-blue-500/40' },
                    { label: 'Replatform', color: 'bg-emerald-500', line: 'border-emerald-500/40' },
                    { label: 'Refactor', color: 'bg-purple-500', line: 'border-purple-500/40' },
                    { label: 'Relocate', color: 'bg-amber-500', line: 'border-amber-500/40' },
                    { label: 'Retire', color: 'bg-red-500', line: 'border-red-500/40' },
                  ].map((s, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div className={`w-12 h-px ${s.line} border-t border-dashed`} />
                      <div className={`${s.color} rounded-full w-2 h-2`} />
                      <span className="text-[10px] font-semibold text-slate-400">{s.label}</span>
                      <ArrowRight className="w-3 h-3 text-slate-600" />
                      <div className={`w-12 h-px ${s.line} border-t border-dashed`} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Target: Cloud Services */}
              <div className="flex-1 max-w-[320px]">
                <div className="text-center mb-4">
                  <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-4 py-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">{currentProvider.label}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  {archData?.service_summary?.map((svc, i) => {
                    const style = getServiceStyle(svc.target_service);
                    return (
                      <div key={i} className={`${style.color} rounded-xl px-4 py-3 border flex items-center justify-between group hover:scale-[1.01] transition-transform`}>
                        <div className="flex items-center gap-3">
                          <span className="text-lg">{style.icon}</span>
                          <div>
                            <div className="text-xs font-bold text-slate-300 max-w-[180px] truncate" title={svc.target_service}>{svc.target_service}</div>
                            <div className="text-[10px] text-slate-500">${svc.avg_monthly_cost}/mo avg</div>
                          </div>
                        </div>
                        <div className="bg-emerald-500/20 rounded-full px-2.5 py-0.5 text-[10px] font-bold text-emerald-400">{svc.server_count}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'ai' && (
        <div className="bg-[#131826] rounded-2xl p-8 border border-white/[0.05] shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2"><Bot className="w-5 h-5 text-indigo-400" /> AI Architecture ({currentProvider.label})</h3>
              <p className="text-sm text-slate-400 mt-1">Gemini analyzes 10,000 servers and generates a {currentProvider.label}-specific architecture document.</p>
            </div>
            <button onClick={generateAiArch} disabled={aiLoading} className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 text-white px-6 py-3 rounded-xl text-sm font-bold flex items-center gap-2 transition-all shadow-lg shadow-indigo-500/20">
              {aiLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</> : <><Zap className="w-4 h-4" /> Generate for {currentProvider.label}</>}
            </button>
          </div>
          
          {aiLoading && (
            <div className="bg-slate-900/50 rounded-xl p-12 text-center border border-white/5">
              <Loader2 className="w-12 h-12 text-indigo-400 mx-auto mb-4 animate-spin" />
              <div className="text-lg font-bold text-white mb-2">Gemini is analyzing your infrastructure...</div>
              <div className="text-sm text-slate-400">Querying 10,000 servers, risk scores, and workload patterns from BigQuery for {currentProvider.label}</div>
            </div>
          )}

          {aiArch && !aiLoading && (
            <div className="bg-slate-900/50 rounded-xl border border-white/5 overflow-hidden flex flex-col">
              <div className="flex flex-col border-b border-white/5 bg-slate-800/50">
                <div className="flex items-center justify-between px-5 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Generated by Gemini • {currentProvider.label}</span>
                  </div>
                  <div className="flex gap-2 bg-[#131826] p-1 rounded-lg border border-white/5">
                    <button onClick={() => setAiSubTab('diagram')} className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${aiSubTab === 'diagram' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}>Diagram</button>
                    <button onClick={() => setAiSubTab('analysis')} className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${aiSubTab === 'analysis' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}>Analysis</button>
                  </div>
                  {aiSubTab === 'diagram' && (
                    <>
                      <button onClick={() => setIsFullscreen(true)} className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors bg-slate-700/50 px-3 py-1.5 rounded-lg border border-white/10 hover:bg-slate-700">
                        <Maximize2 className="w-3 h-3" /> Full Screen
                      </button>
                      <a href={getMermaidLiveUrl(mermaidCode)} target="_blank" rel="noopener noreferrer" className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors bg-slate-700/50 px-3 py-1.5 rounded-lg border border-white/10 hover:bg-slate-700">
                        <ExternalLink className="w-3 h-3" /> Mermaid Live
                      </a>
                    </>
                  )}
                  <button onClick={() => {
                      const textToCopy = aiSubTab === 'diagram' ? (mermaidCode || aiArch) : (markdownText || aiArch);
                      navigator.clipboard.writeText(textToCopy);
                    }} className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors bg-slate-700/50 px-3 py-1.5 rounded-lg border border-white/10 hover:bg-slate-700">
                    <Copy className="w-3 h-3" /> Copy {aiSubTab === 'diagram' ? 'Mermaid' : 'Text'}
                  </button>
                </div>
              </div>
              <div className="p-8 max-h-[800px] overflow-y-auto custom-scrollbar">
                {aiSubTab === 'diagram' && (
                  <div>
                    <div className="mb-4 text-xs text-slate-500 bg-slate-800/50 p-3 rounded-lg border border-white/5">
                      <span className="font-semibold text-slate-300">Tip:</span> To edit in <span className="text-white">Draw.io</span>, click "Copy Mermaid" above, then in Draw.io go to <span className="text-indigo-300">Arrange → Insert → Advanced → Mermaid</span> and paste the code.
                    </div>
                    {mermaidCode ? <Mermaid chart={mermaidCode} /> : <div className="text-sm text-slate-400 italic">No valid Mermaid diagram found in the output.</div>}
                  </div>
                )}
                {aiSubTab === 'analysis' && (
                  <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdownText || aiArch}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {!aiArch && !aiLoading && (
            <div className="bg-gradient-to-br from-slate-900/50 to-indigo-900/10 rounded-xl p-12 text-center border border-indigo-500/10">
              <Bot className="w-16 h-16 text-slate-700 mx-auto mb-4" />
              <div className="text-lg font-bold text-slate-400 mb-2">Generate {currentProvider.label} Architecture</div>
              <div className="text-sm text-slate-500 max-w-md mx-auto">
                Click the button above to generate a comprehensive {currentProvider.label} architecture using real server data from BigQuery.
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'mapping' && (
        <div className="bg-[#131826] rounded-2xl p-8 border border-white/[0.05] shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">Component Mapping Table</h3>
              <p className="text-sm text-slate-400 mt-1">
                {filterService !== 'All' ? `Showing ${filteredMappings.length} workloads → ${filterService}` : `All ${archData?.mappings?.length || 0} AI-mapped workloads → ${currentProvider.label}`}
              </p>
            </div>
            <div className="flex gap-2 items-center">
              <select value={filterService} onChange={e => setFilterService(e.target.value)}
                className="bg-slate-900 border border-white/10 rounded-lg px-4 py-2 text-xs text-white">
                <option value="All">All Services ({archData?.mappings?.length || 0})</option>
                {archData?.service_summary?.map((s, i) => (
                  <option key={i} value={s.target_service}>{s.target_service} ({s.server_count})</option>
                ))}
              </select>
              {filterService !== 'All' && (
                <button onClick={() => setFilterService('All')} className="text-xs text-indigo-400 hover:text-indigo-300">Clear</button>
              )}
            </div>
          </div>
          <div className="overflow-x-auto max-h-[600px] custom-scrollbar rounded-xl border border-white/5">
            <table className="w-full text-sm text-left">
              <thead className="text-slate-400 bg-slate-900/80 border-b border-white/10 sticky top-0 z-10 text-xs">
                <tr>
                  <th className="p-3 w-8"></th>
                  <th className="p-3">Source VM</th>
                  <th className="p-3">Workload</th>
                  <th className="p-3">Source Technology</th>
                  <th className="p-3">Strategy</th>
                  <th className="p-3 text-center">→</th>
                  <th className="p-3">{currentProvider.label} Target</th>
                  <th className="p-3">Machine Type</th>
                  <th className="p-3 text-right">Cost/mo</th>
                </tr>
              </thead>
              <tbody className="text-slate-300 divide-y divide-white/5 bg-[#0f141f]">
                {filteredMappings.length === 0 && (
                  <tr><td colSpan={9} className="p-8 text-center text-slate-500">No mappings found.</td></tr>
                )}
                {filteredMappings.map((m, i) => {
                  const style = getServiceStyle(m.target_service);
                  const strategy = (m.recommended_strategy || '').toLowerCase();
                  const strategyColor = STRATEGY_COLORS[strategy] || 'bg-slate-500/15 text-slate-400 border-slate-500/30';
                  return (
                    <React.Fragment key={i}>
                      <tr className="hover:bg-white/[0.03] cursor-pointer" onClick={() => toggleRow(i)}>
                        <td className="p-3 text-center">
                          {expandedRows[i] ? <ChevronDown className="w-3 h-3 text-slate-500" /> : <ChevronRight className="w-3 h-3 text-slate-500" />}
                        </td>
                        <td className="p-3 font-medium text-indigo-300">
                          <div className="flex items-center gap-2">
                            <Server className="w-3 h-3 text-slate-500 flex-shrink-0" />
                            <span className="truncate max-w-[150px]" title={m.source_name}>{m.source_name}</span>
                          </div>
                        </td>
                        <td className="p-3"><span className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded-full text-[10px] font-bold">{m.workload_type || '—'}</span></td>
                        <td className="p-3 text-xs text-slate-400 max-w-[200px] truncate" title={m.source_tech}>{m.source_tech || '—'}</td>
                        <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${strategyColor}`}>{m.recommended_strategy || '—'}</span></td>
                        <td className="p-3 text-center"><ArrowRight className="w-4 h-4 text-indigo-400 mx-auto" /></td>
                        <td className="p-3 font-medium text-emerald-300">
                          <div className="flex items-center gap-2">
                            <span>{style.icon}</span>
                            <span className="truncate max-w-[180px]" title={m.target_service}>{m.target_service}</span>
                          </div>
                        </td>
                        <td className="p-3 text-xs text-slate-400">{m.target_machine_type || '—'}</td>
                        <td className="p-3 text-right font-bold text-emerald-400">${m.cost_estimate_monthly?.toLocaleString() || '0'}</td>
                      </tr>
                      {expandedRows[i] && (
                        <tr>
                          <td colSpan={9} className="p-0">
                            <div className="bg-indigo-500/5 border-l-2 border-indigo-500/30 mx-4 my-2 rounded-r-xl p-4">
                              <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider mb-2">🧠 AI Reasoning (Gemini)</div>
                              <div className="text-xs text-slate-300 leading-relaxed">{m.ai_reasoning || 'No reasoning available.'}</div>
                              {m.rightsizing_recommendation && (
                                <div className="mt-3 pt-3 border-t border-white/5">
                                  <div className="text-[10px] font-bold text-amber-400 uppercase tracking-wider mb-1">📐 Right-Sizing</div>
                                  <div className="text-xs text-slate-400">{m.rightsizing_recommendation}</div>
                                </div>
                              )}
                              <div className="flex gap-4 mt-3 pt-3 border-t border-white/5 text-[10px] text-slate-500">
                                <span>Server ID: <strong className="text-slate-300">{m.server_id || '—'}</strong></span>
                                <span>Region: <strong className="text-slate-300">{m.target_region || '—'}</strong></span>
                                <span>Cost: <strong className="text-emerald-400">${m.cost_estimate_monthly?.toLocaleString()}/mo</strong></span>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {isFullscreen && aiSubTab === 'diagram' && mermaidCode && (
        <div className="fixed inset-0 z-50 bg-[#0f141f] flex flex-col">
          <div className="flex items-center justify-between p-4 bg-slate-900 border-b border-white/10">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Maximize2 className="w-5 h-5 text-indigo-400" /> Full Screen Architecture
            </h2>
            <div className="flex items-center gap-3">
              <a href={getMermaidLiveUrl(mermaidCode)} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2">
                <ExternalLink className="w-4 h-4" /> Open in Mermaid Live
              </a>
              <button onClick={() => setIsFullscreen(false)} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-full text-slate-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-auto p-8 custom-scrollbar">
            <Mermaid chart={mermaidCode} />
          </div>
        </div>
      )}
    </main>
  );
}
