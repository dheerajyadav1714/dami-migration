import React, { useState } from 'react';
import { Cable, Check, X, ExternalLink, Webhook, CheckCircle2, Settings, Loader2 } from 'lucide-react';

const INTEGRATIONS = [
  { name: 'Jira', icon: '📋', desc: 'Auto-create migration tasks and track wave progress in Jira boards.', status: 'available', category: 'Project Management', configFields: ['Jira URL', 'Project Key', 'API Token'] },
  { name: 'Slack', icon: '💬', desc: 'Push real-time migration notifications, alerts, and agent summaries to Slack channels.', status: 'available', category: 'Communication', configFields: ['Webhook URL', 'Channel Name'] },
  { name: 'ServiceNow', icon: '🔧', desc: 'Sync CMDB records and create change requests for each cutover wave.', status: 'available', category: 'ITSM', configFields: ['Instance URL', 'Username', 'Password'] },
  { name: 'PagerDuty', icon: '🚨', desc: 'Route critical migration alerts and cutover failure notifications.', status: 'coming_soon', category: 'Monitoring' },
  { name: 'Terraform Cloud', icon: '🏗️', desc: 'Deploy generated IaC directly through Terraform Cloud workspaces.', status: 'available', category: 'Infrastructure', configFields: ['Organization', 'Workspace', 'API Token'] },
  { name: 'GitHub Actions', icon: '🔄', desc: 'Trigger CI/CD pipelines for migration artifact deployment.', status: 'available', category: 'CI/CD', configFields: ['Repository URL', 'PAT Token', 'Workflow File'] },
  { name: 'Datadog', icon: '📊', desc: 'Monitor post-migration application performance and health.', status: 'coming_soon', category: 'Monitoring' },
  { name: 'Looker Studio', icon: '📈', desc: 'Embed Looker dashboards for executive migration reporting.', status: 'available', category: 'Analytics', configFields: ['Dashboard URL', 'Embed Token'] },
];

export default function Integrations() {
  const [activeTab, setActiveTab] = useState('all');
  const [configuring, setConfiguring] = useState(null);
  const [connected, setConnected] = useState({});
  const [saving, setSaving] = useState(false);
  const [formValues, setFormValues] = useState({});

  const categories = ['all', ...Array.from(new Set(INTEGRATIONS.map(i => i.category)))];
  const filtered = activeTab === 'all' ? INTEGRATIONS : INTEGRATIONS.filter(i => i.category === activeTab);

  const handleConfigure = (int, index) => {
    if (connected[int.name]) {
      // Disconnect
      setConnected(prev => { const n = { ...prev }; delete n[int.name]; return n; });
      return;
    }
    setConfiguring(configuring === index ? null : index);
    setFormValues({});
  };

  const handleSave = (int) => {
    setSaving(true);
    setTimeout(() => {
      setConnected(prev => ({ ...prev, [int.name]: true }));
      setConfiguring(null);
      setSaving(false);
    }, 1500);
  };

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Integrations</h1>
        <p className="text-slate-400 font-medium">Connect D.A.M.I. to your existing DevOps toolchain — Jira, Slack, ServiceNow, Terraform, and more.</p>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* Connected count */}
      <div className="flex items-center gap-4 mb-6">
        <div className="bg-[#131826] rounded-xl px-5 py-3 border border-white/[0.05] flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <div>
            <div className="text-xs text-slate-400">Connected</div>
            <div className="text-xl font-bold text-white">{Object.keys(connected).length} / {INTEGRATIONS.filter(i => i.status === 'available').length}</div>
          </div>
        </div>
      </div>

      <div className="flex gap-2 mb-8 overflow-x-auto">
        {categories.map(c => (
          <button key={c} onClick={() => setActiveTab(c)} className={`px-4 py-2 rounded-lg text-xs font-bold capitalize whitespace-nowrap transition-all ${activeTab === c ? 'bg-indigo-600/20 border border-indigo-500/50 text-white' : 'bg-[#131826] border border-white/5 text-slate-400 hover:text-white'}`}>{c}</button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((int, i) => {
          const isConnected = connected[int.name];
          const isConfiguring = configuring === i;
          return (
            <div key={i} className={`bg-[#131826] rounded-xl p-6 border transition-all ${isConnected ? 'border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : isConfiguring ? 'border-indigo-500/30' : 'border-white/[0.05] hover:border-indigo-500/30'}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{int.icon}</span>
                  <div>
                    <div className="font-bold text-white">{int.name}</div>
                    <div className="text-xs text-slate-500">{int.category}</div>
                  </div>
                </div>
                {isConnected ? (
                  <span className="text-xs font-bold bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded-full flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Connected</span>
                ) : int.status === 'available' ? (
                  <span className="text-xs font-bold bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded-full">Available</span>
                ) : (
                  <span className="text-xs font-bold bg-slate-500/10 text-slate-400 px-2 py-1 rounded-full">Coming Soon</span>
                )}
              </div>
              <p className="text-sm text-slate-400 mb-4">{int.desc}</p>

              {/* Configuration form */}
              {isConfiguring && int.configFields && (
                <div className="mb-4 space-y-2 p-3 bg-slate-900/50 rounded-lg border border-white/5">
                  {int.configFields.map((field, fi) => (
                    <div key={fi}>
                      <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide">{field}</label>
                      <input 
                        type={field.toLowerCase().includes('token') || field.toLowerCase().includes('password') ? 'password' : 'text'}
                        placeholder={`Enter ${field}...`}
                        value={formValues[field] || ''}
                        onChange={e => setFormValues(prev => ({ ...prev, [field]: e.target.value }))}
                        className="w-full bg-[#0b0f19] border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 mt-1"
                      />
                    </div>
                  ))}
                  <button 
                    onClick={() => handleSave(int)} 
                    disabled={saving}
                    className="w-full mt-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-bold transition-colors flex items-center justify-center gap-2"
                  >
                    {saving ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Connecting...</> : <><CheckCircle2 className="w-3.5 h-3.5" /> Save & Connect</>}
                  </button>
                </div>
              )}

              <button 
                onClick={() => handleConfigure(int, i)} 
                disabled={int.status !== 'available'}
                className={`w-full border px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                  isConnected 
                    ? 'bg-red-600/10 border-red-500/30 text-red-400 hover:bg-red-600/20' 
                    : 'bg-slate-900/50 border-white/10 text-slate-300 hover:bg-indigo-600/10 hover:border-indigo-500/30 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed'
                }`}
              >
                {isConnected ? <><X className="w-3.5 h-3.5" /> Disconnect</> : int.status === 'available' ? <><Settings className="w-3.5 h-3.5" /> Configure</> : <><Webhook className="w-3.5 h-3.5" /> Notify Me</>}
              </button>
            </div>
          );
        })}
      </div>
    </main>
  );
}
