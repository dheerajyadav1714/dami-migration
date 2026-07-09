import React, { useState } from 'react';
import axios from 'axios';
import { Fingerprint, ShieldAlert, Globe2, Lock, Loader2, Copy, Check, AlertTriangle, CheckCircle2 } from 'lucide-react';

const SAMPLE_SCHEMA = `CREATE TABLE customers (
  id INT PRIMARY KEY,
  full_name VARCHAR(100),
  email VARCHAR(255),
  phone VARCHAR(20),
  date_of_birth DATE,
  ssn CHAR(11),
  credit_card_number VARCHAR(19),
  address TEXT,
  ip_address VARCHAR(45),
  salary DECIMAL(10,2),
  medical_record_id VARCHAR(50),
  passport_number VARCHAR(20)
);`;

const REGIONS = [
  { id: 'us-central1', name: 'Iowa (US)', laws: ['CCPA', 'HIPAA'] },
  { id: 'europe-west1', name: 'Belgium (EU)', laws: ['GDPR', 'EU Data Act'] },
  { id: 'asia-south1', name: 'Mumbai (India)', laws: ['DPDP Act 2023', 'RBI Guidelines'] },
  { id: 'asia-southeast1', name: 'Singapore', laws: ['PDPA'] },
  { id: 'australia-southeast1', name: 'Sydney', laws: ['Privacy Act 1988'] },
];

export default function DataSensitivity() {
  const [schema, setSchema] = useState('');
  const [targetRegion, setTargetRegion] = useState('us-central1');
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [copied, setCopied] = useState(false);

  const analyze = async () => {
    if (!schema.trim()) return;
    setAnalyzing(true);
    try {
      const prompt = `You are a data privacy and compliance expert. Analyze this database schema and identify ALL columns containing PII (Personally Identifiable Information), PHI (Protected Health Information), or PCI (Payment Card Industry) data.

Schema:
${schema}

Target GCP Region: ${targetRegion} (${REGIONS.find(r => r.id === targetRegion)?.name})
Applicable Laws: ${REGIONS.find(r => r.id === targetRegion)?.laws.join(', ')}

For each column, respond in this EXACT format (one per line):
COLUMN: column_name | CLASSIFICATION: PII/PHI/PCI/FINANCIAL/NONE | SENSITIVITY: CRITICAL/HIGH/MEDIUM/LOW | REGULATION: which regulation applies | RECOMMENDATION: what to do

After all columns, add:
SUMMARY: total PII columns found, overall risk level, and key compliance actions needed for the target region.

RESIDENCY_CHECK: Whether this data can legally be stored in the target region, and what conditions apply.`;

      const res = await axios.post('http://localhost:8000/api/chat', { prompt });
      const reply = res.data?.reply || 'Analysis failed.';
      
      // Parse the response
      const columns = [];
      const lines = reply.split('\n');
      let summary = '';
      let residency = '';
      
      lines.forEach(line => {
        if (line.startsWith('COLUMN:')) {
          const parts = line.replace('COLUMN:', '').split('|').map(s => s.trim());
          columns.push({
            name: parts[0] || '',
            classification: (parts[1] || '').replace('CLASSIFICATION:', '').trim(),
            sensitivity: (parts[2] || '').replace('SENSITIVITY:', '').trim(),
            regulation: (parts[3] || '').replace('REGULATION:', '').trim(),
            recommendation: (parts[4] || '').replace('RECOMMENDATION:', '').trim(),
          });
        }
        if (line.startsWith('SUMMARY:')) summary = line.replace('SUMMARY:', '').trim();
        if (line.startsWith('RESIDENCY_CHECK:')) residency = line.replace('RESIDENCY_CHECK:', '').trim();
      });

      setResults({ columns, summary, residency, rawResponse: reply });
    } catch {
      setResults({ columns: [], summary: 'Failed to analyze. Check backend.', residency: '', rawResponse: '' });
    } finally {
      setAnalyzing(false);
    }
  };

  const sensColor = (s) => {
    const sl = s?.toLowerCase() || '';
    if (sl.includes('critical')) return 'bg-red-500/10 text-red-400';
    if (sl.includes('high')) return 'bg-orange-500/10 text-orange-400';
    if (sl.includes('medium')) return 'bg-yellow-500/10 text-yellow-400';
    return 'bg-green-500/10 text-green-400';
  };

  const classColor = (c) => {
    const cl = c?.toLowerCase() || '';
    if (cl.includes('pci')) return 'bg-red-500/10 text-red-400';
    if (cl.includes('phi')) return 'bg-purple-500/10 text-purple-400';
    if (cl.includes('pii')) return 'bg-amber-500/10 text-amber-400';
    if (cl.includes('financial')) return 'bg-blue-500/10 text-blue-400';
    return 'bg-slate-500/10 text-slate-400';
  };

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 tracking-tight mb-2">Data Sensitivity Scanner</h1>
        <p className="text-slate-400 font-medium">AI-powered PII/PHI/PCI detection in database schemas — identify compliance risks before migrating sensitive data to the cloud.</p>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Input */}
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Fingerprint className="w-5 h-5 text-purple-400" /> Input Schema</h3>
          
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1">
              <label className="text-xs text-slate-400 font-bold mb-1 block">Target GCP Region</label>
              <select value={targetRegion} onChange={e => setTargetRegion(e.target.value)} className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white">
                {REGIONS.map(r => <option key={r.id} value={r.id}>{r.name} — {r.laws.join(', ')}</option>)}
              </select>
            </div>
          </div>

          <textarea
            value={schema}
            onChange={e => setSchema(e.target.value)}
            placeholder="Paste your CREATE TABLE DDL, column list, or schema description here..."
            rows={12}
            className="w-full bg-[#0b0f19] border border-white/10 rounded-xl px-4 py-3 text-xs text-slate-200 font-mono placeholder-slate-600 focus:outline-none focus:border-purple-500 resize-none mb-4 custom-scrollbar"
          />

          <div className="flex gap-2">
            <button onClick={analyze} disabled={analyzing || !schema.trim()} className="flex-1 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white px-6 py-3 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2 shadow-lg">
              {analyzing ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing with Gemini...</> : <><ShieldAlert className="w-4 h-4" /> Scan for Sensitive Data</>}
            </button>
            <button onClick={() => setSchema(SAMPLE_SCHEMA)} className="bg-slate-800 border border-white/10 text-slate-300 hover:text-white px-4 py-3 rounded-xl text-xs font-bold transition-colors">
              Load Sample
            </button>
          </div>
        </div>

        {/* Region Info */}
        <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Globe2 className="w-5 h-5 text-blue-400" /> Data Residency Laws</h3>
          <div className="space-y-3">
            {REGIONS.map(r => (
              <div key={r.id} className={`p-4 rounded-xl border ${r.id === targetRegion ? 'bg-purple-500/5 border-purple-500/20' : 'bg-slate-900/30 border-white/5'}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-white text-sm">{r.name}</span>
                  {r.id === targetRegion && <span className="text-[10px] font-bold bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded-full">Selected</span>}
                </div>
                <div className="flex gap-1.5 flex-wrap">
                  {r.laws.map((law, i) => <span key={i} className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded">{law}</span>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      {results && (
        <>
          {/* Summary */}
          {results.summary && (
            <div className="bg-purple-500/5 rounded-xl p-6 border border-purple-500/20 mb-8">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2"><ShieldAlert className="w-5 h-5 text-purple-400" /> Analysis Summary</h3>
              <p className="text-sm text-slate-300">{results.summary}</p>
              {results.residency && (
                <div className="mt-3 p-3 bg-slate-900/30 rounded-lg border border-white/5">
                  <div className="text-xs font-bold text-amber-400 mb-1">🌍 Data Residency Check</div>
                  <p className="text-xs text-slate-400">{results.residency}</p>
                </div>
              )}
            </div>
          )}

          {/* Column Analysis Table */}
          {results.columns.length > 0 && (
            <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] mb-8">
              <h3 className="text-lg font-bold text-white mb-4">Column-by-Column Analysis</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="text-slate-400 bg-slate-900 border-b border-white/10">
                    <tr><th className="p-3">Column</th><th className="p-3">Classification</th><th className="p-3">Sensitivity</th><th className="p-3">Regulation</th><th className="p-3">Recommendation</th></tr>
                  </thead>
                  <tbody className="text-slate-300 divide-y divide-white/5">
                    {results.columns.map((col, i) => (
                      <tr key={i} className="hover:bg-white/5">
                        <td className="p-3 font-mono font-bold text-purple-300">{col.name}</td>
                        <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${classColor(col.classification)}`}>{col.classification}</span></td>
                        <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${sensColor(col.sensitivity)}`}>{col.sensitivity}</span></td>
                        <td className="p-3 text-slate-400">{col.regulation}</td>
                        <td className="p-3 text-slate-400 max-w-xs">{col.recommendation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Raw AI Response */}
          {results.rawResponse && (
            <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05]">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2"><Lock className="w-5 h-5 text-slate-400" /> Full Gemini Analysis</h3>
                <button onClick={() => { navigator.clipboard.writeText(results.rawResponse); setCopied(true); setTimeout(() => setCopied(false), 2000); }} className="text-xs text-slate-400 hover:text-white transition-colors flex items-center gap-1">
                  {copied ? <><Check className="w-3 h-3 text-emerald-400" /> Copied</> : <><Copy className="w-3 h-3" /> Copy</>}
                </button>
              </div>
              <pre className="text-xs text-slate-400 whitespace-pre-wrap font-mono bg-slate-900/50 rounded-lg p-4 max-h-[300px] overflow-y-auto custom-scrollbar">{results.rawResponse}</pre>
            </div>
          )}
        </>
      )}
    </main>
  );
}
