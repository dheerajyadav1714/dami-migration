import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { ShieldCheck, CheckCircle2, AlertTriangle, XCircle, Lock, Server, Eye, Code, Zap } from 'lucide-react';
import { ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip } from 'recharts';

const FRAMEWORKS = {
  "HIPAA": {
    icon: "🏥", color: "#ef4444",
    controls: [
      { id: "164.312(a)(1)", name: "Access Control", gcp: "Cloud IAM + Context-Aware Access", status: "pass" },
      { id: "164.312(a)(2)(iv)", name: "Encryption at Rest", gcp: "CMEK (Cloud KMS)", status: "pass" },
      { id: "164.312(e)(1)", name: "Transmission Security", gcp: "VPC Service Controls + TLS 1.3", status: "pass" },
      { id: "164.308(a)(1)", name: "Security Management", gcp: "Security Command Center Premium", status: "review" },
      { id: "164.312(b)", name: "Audit Controls", gcp: "Cloud Audit Logs + Chronicle SIEM", status: "pass" },
      { id: "164.310(d)(1)", name: "Device & Media Controls", gcp: "Confidential VMs + Shielded VMs", status: "review" },
    ]
  },
  "PCI-DSS": {
    icon: "💳", color: "#f59e0b",
    controls: [
      { id: "Req 1", name: "Network Segmentation", gcp: "VPC Firewall Rules + Hierarchical Policies", status: "pass" },
      { id: "Req 3", name: "Protect Stored Data", gcp: "CMEK + DLP API", status: "pass" },
      { id: "Req 6", name: "Secure Development", gcp: "Binary Authorization + Artifact Registry", status: "review" },
      { id: "Req 7", name: "Access Restriction", gcp: "IAM Conditions + VPC-SC Perimeters", status: "pass" },
      { id: "Req 8", name: "Authentication", gcp: "Cloud Identity + MFA Enforcement", status: "pass" },
      { id: "Req 10", name: "Logging & Monitoring", gcp: "Cloud Logging + Cloud Monitoring", status: "pass" },
    ]
  },
  "SOC2": {
    icon: "🔒", color: "#3b82f6",
    controls: [
      { id: "CC6.1", name: "Logical Access", gcp: "Cloud IAM + BeyondCorp", status: "pass" },
      { id: "CC6.6", name: "System Boundaries", gcp: "VPC Service Controls", status: "pass" },
      { id: "CC7.2", name: "System Monitoring", gcp: "Cloud Monitoring + SCC", status: "pass" },
      { id: "CC8.1", name: "Change Management", gcp: "Cloud Deploy + Config Connector", status: "review" },
      { id: "CC6.3", name: "Role-Based Access", gcp: "IAM Custom Roles", status: "pass" },
    ]
  },
  "ISO27001": {
    icon: "🌐", color: "#10b981",
    controls: [
      { id: "A.9.1", name: "Access Control Policy", gcp: "Organization Policies + IAM", status: "pass" },
      { id: "A.10.1", name: "Cryptographic Controls", gcp: "Cloud KMS + Cloud HSM", status: "pass" },
      { id: "A.12.4", name: "Logging & Monitoring", gcp: "Cloud Audit Logs", status: "pass" },
      { id: "A.14.1", name: "Security in Dev", gcp: "Artifact Analysis + Binary Auth", status: "review" },
      { id: "A.13.1", name: "Network Security", gcp: "VPC + Cloud Armor", status: "pass" },
    ]
  }
};

const HEATMAP_DATA = [
  { workload: 'Payment App', hipaa: 'high', pci: 'critical', soc2: 'medium', iso: 'medium' },
  { workload: 'Web Frontend', hipaa: 'low', pci: 'medium', soc2: 'low', iso: 'low' },
  { workload: 'Oracle Database', hipaa: 'critical', pci: 'critical', soc2: 'high', iso: 'high' },
  { workload: 'LDAP Server', hipaa: 'medium', pci: 'high', soc2: 'high', iso: 'medium' },
  { workload: 'Redis Cache', hipaa: 'low', pci: 'medium', soc2: 'low', iso: 'low' },
  { workload: 'RabbitMQ', hipaa: 'low', pci: 'low', soc2: 'low', iso: 'low' },
];

const RISK_BG = { critical: 'bg-red-500/30 text-red-300', high: 'bg-orange-500/20 text-orange-300', medium: 'bg-yellow-500/15 text-yellow-300', low: 'bg-green-500/15 text-green-300' };

const SECURITY_IAC = `# Auto-Generated Security IaC — VPC Service Controls
resource "google_access_context_manager_service_perimeter" "dami_perimeter" {
  parent = "accessPolicies/\${var.access_policy_id}"
  name   = "accessPolicies/\${var.access_policy_id}/servicePerimeters/dami_perimeter"
  title  = "D.A.M.I. Migration Perimeter"
  
  status {
    restricted_services = [
      "bigquery.googleapis.com",
      "storage.googleapis.com",
      "compute.googleapis.com",
    ]
    resources = ["projects/\${var.project_number}"]
  }
}`;

const GAP_ANALYSIS = [
  { framework: 'HIPAA', gap: 'Security Management Process', severity: 'high', remediation: 'Deploy SCC Premium + enable continuous monitoring', status: 'In Progress' },
  { framework: 'HIPAA', gap: 'Device & Media Controls', severity: 'medium', remediation: 'Enable Confidential VMs for PHI workloads', status: 'Planned' },
  { framework: 'PCI-DSS', gap: 'Secure Development (Req 6)', severity: 'medium', remediation: 'Configure Binary Authorization + vulnerability scanning', status: 'Planned' },
  { framework: 'SOC2', gap: 'Change Management (CC8.1)', severity: 'low', remediation: 'Implement Cloud Deploy pipelines with approval gates', status: 'Planned' },
  { framework: 'ISO27001', gap: 'Security in Development', severity: 'medium', remediation: 'Enable Artifact Analysis for container images', status: 'In Progress' },
];

export default function ComplianceAndSecurity() {
  const [selectedFramework, setSelectedFramework] = useState('HIPAA');

  const radarData = Object.entries(FRAMEWORKS).map(([name, f]) => ({
    framework: name,
    score: Math.round((f.controls.filter(c => c.status === 'pass').length / f.controls.length) * 100)
  }));

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">Compliance & Security Posture</h1>
        <p className="text-slate-400 font-medium">Maps workloads to compliance frameworks and shows security control readiness for each migration wave.</p>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* Compliance Framework Coverage Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {Object.entries(FRAMEWORKS).map(([name, f]) => {
          const passCount = f.controls.filter(c => c.status === 'pass').length;
          const reviewCount = f.controls.filter(c => c.status === 'review').length;
          const pct = Math.round((passCount / f.controls.length) * 100);
          return (
            <button key={name} onClick={() => setSelectedFramework(name)}
              className={`p-5 rounded-xl border text-left transition-all ${selectedFramework === name ? 'bg-indigo-600/10 border-indigo-500/30 ring-1 ring-indigo-500/30' : 'bg-[#131826] border-white/[0.05] hover:bg-white/[0.02]'}`}>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">{f.icon}</span>
                <div className="font-bold text-white">{name}</div>
              </div>
              <div className="text-3xl font-black mb-1" style={{color: pct >= 80 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444'}}>{pct}%</div>
              <div className="text-xs text-slate-400 mb-2">Auto-mapped controls</div>
              <div className="flex gap-2 text-[10px]">
                <span className="text-emerald-400">✅ {passCount} Automated</span>
                <span className="text-amber-400">👁️ {reviewCount} Review</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Radar + Control Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-lg font-bold text-white mb-4">Cross-Framework Radar</h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis dataKey="framework" stroke="#94a3b8" tick={{fontSize:11}} />
                <PolarRadiusAxis domain={[0, 100]} stroke="#334155" tick={{fontSize:9}} />
                <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
                <Tooltip contentStyle={{backgroundColor:'#0f172a', borderColor:'#1e293b', color:'#fff'}} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] lg:col-span-2">
          <h3 className="text-lg font-bold text-white mb-4">{FRAMEWORKS[selectedFramework].icon} {selectedFramework} — GCP Control Mapping</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-slate-400 bg-slate-900 border-b border-white/10">
                <tr><th className="p-3">ID</th><th className="p-3">Control</th><th className="p-3">GCP Service</th><th className="p-3">Status</th></tr>
              </thead>
              <tbody className="text-slate-300 divide-y divide-white/5 bg-[#0f141f]">
                {FRAMEWORKS[selectedFramework].controls.map((c, i) => (
                  <tr key={i} className="hover:bg-white/5">
                    <td className="p-3 font-mono text-indigo-300">{c.id}</td>
                    <td className="p-3 font-medium">{c.name}</td>
                    <td className="p-3 text-slate-400 text-xs">{c.gcp}</td>
                    <td className="p-3">{c.status === 'pass' ? <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400"><CheckCircle2 className="w-3 h-3" /> Auto</span> : <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400"><Eye className="w-3 h-3" /> Review</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Workload Compliance Risk Heatmap */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg mb-8">
        <h3 className="text-xl font-bold text-white mb-4">🔥 Workload Compliance Risk Heatmap</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-slate-400 bg-slate-900 border-b border-white/10">
              <tr><th className="p-3">Workload</th><th className="p-3 text-center">HIPAA</th><th className="p-3 text-center">PCI-DSS</th><th className="p-3 text-center">SOC2</th><th className="p-3 text-center">ISO27001</th></tr>
            </thead>
            <tbody className="text-slate-300 divide-y divide-white/5">
              {HEATMAP_DATA.map((h, i) => (
                <tr key={i}>
                  <td className="p-3 font-medium text-white">{h.workload}</td>
                  {['hipaa', 'pci', 'soc2', 'iso'].map(fw => (
                    <td key={fw} className="p-3 text-center"><span className={`px-3 py-1 rounded text-xs font-bold capitalize ${RISK_BG[h[fw]]}`}>{h[fw]}</span></td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Generated Security IaC */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg mb-8">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><Code className="w-5 h-5 text-emerald-400" /> Generated Security Infrastructure-as-Code</h3>
        <pre className="bg-slate-900/50 rounded-xl p-5 text-xs font-mono text-slate-300 overflow-x-auto border border-white/5 max-h-[300px] custom-scrollbar">{SECURITY_IAC}</pre>
      </div>

      {/* Compliance Gap Analysis */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg mb-8">
        <h3 className="text-xl font-bold text-white mb-4">🔍 Compliance Gap Analysis & Auto-Remediation</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-slate-400 bg-slate-900 border-b border-white/10">
              <tr><th className="p-3">Framework</th><th className="p-3">Gap</th><th className="p-3">Severity</th><th className="p-3">Auto-Remediation</th><th className="p-3">Status</th></tr>
            </thead>
            <tbody className="text-slate-300 divide-y divide-white/5 bg-[#0f141f]">
              {GAP_ANALYSIS.map((g, i) => (
                <tr key={i} className="hover:bg-white/5">
                  <td className="p-3 font-bold text-indigo-300">{g.framework}</td>
                  <td className="p-3">{g.gap}</td>
                  <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-xs font-bold ${g.severity === 'high' ? 'bg-orange-500/10 text-orange-400' : g.severity === 'medium' ? 'bg-amber-500/10 text-amber-400' : 'bg-green-500/10 text-green-400'}`}>{g.severity}</span></td>
                  <td className="p-3 text-xs text-slate-400">{g.remediation}</td>
                  <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-xs font-bold ${g.status === 'In Progress' ? 'bg-blue-500/10 text-blue-400' : 'bg-slate-500/10 text-slate-400'}`}>{g.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Zero-Trust Security Policy Generator */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><Zap className="w-5 h-5 text-amber-400" /> AI Zero-Trust Security Policy Generator</h3>
        <p className="text-sm text-slate-400 mb-4">Gemini-powered policy generation based on your workload profiles and compliance requirements.</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-indigo-500/[0.05] border border-indigo-500/20 rounded-xl p-5">
            <div className="font-bold text-indigo-400 mb-2">🔐 Identity-Aware Proxy</div>
            <div className="text-xs text-slate-400">Auto-generated BeyondCorp access policies for each application based on user roles and device trust.</div>
          </div>
          <div className="bg-emerald-500/[0.05] border border-emerald-500/20 rounded-xl p-5">
            <div className="font-bold text-emerald-400 mb-2">🛡️ VPC Service Controls</div>
            <div className="text-xs text-slate-400">Perimeter definitions auto-generated based on data sensitivity classification and compliance framework requirements.</div>
          </div>
          <div className="bg-amber-500/[0.05] border border-amber-500/20 rounded-xl p-5">
            <div className="font-bold text-amber-400 mb-2">📋 Org Policies</div>
            <div className="text-xs text-slate-400">Organization Policy constraints enforcing encryption, region restrictions, and service restrictions.</div>
          </div>
        </div>
      </div>
    </main>
  );
}
