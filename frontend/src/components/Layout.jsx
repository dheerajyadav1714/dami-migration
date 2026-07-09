import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { 
  CloudLightning, 
  LayoutDashboard, 
  UploadCloud, 
  Layers, 
  Network, 
  ShieldCheck, 
  User, 
  Server,
  AlertTriangle,
  FileCode2,
  DollarSign,
  Key,
  CheckSquare,
  MessageSquare,
  Code,
  Zap,
  Cable,
  Users,
  Activity,
  BrainCircuit,
  Bot,
  ChevronLeft,
  ChevronRight,
  Ghost,
  Leaf,
  Shield,
  Calendar,
  Fingerprint,
  CreditCard
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', name: 'Executive Dashboard', icon: LayoutDashboard },
  { path: '/ingestion-center', name: 'Ingestion Center', icon: UploadCloud },
  { path: '/server-inventory', name: 'Server Inventory', icon: Server },
  { path: '/dependency-map', name: 'Dependency Map', icon: Network },
  { path: '/shadow-it', name: 'Shadow IT Detector', icon: Ghost },
  { path: '/data-sensitivity', name: 'Data Sensitivity', icon: Fingerprint },
  { path: '/risk-assessment', name: 'Risk Assessment', icon: AlertTriangle },
  { path: '/migration-wave-plan', name: 'Migration Wave Plan', icon: Layers },
  { path: '/blackout-calendar', name: 'Blackout Calendar', icon: Calendar },
  { path: '/quota-checker', name: 'GCP Quota Checker', icon: Shield },
  { path: '/target-architecture', name: 'Target Architecture', icon: Network },
  { path: '/iac-and-runbooks', name: 'IaC & Runbooks', icon: FileCode2 },
  { path: '/cutover-simulation', name: 'Cutover Simulation', icon: Zap },
  { path: '/validation', name: 'Validation', icon: CheckSquare },
  { path: '/finops-and-tco', name: 'FinOps & TCO', icon: DollarSign },
  { path: '/vmware-license', name: 'VMware License Shock', icon: CreditCard },
  { path: '/carbon-footprint', name: 'Carbon Footprint', icon: Leaf },
  { path: '/compliance-and-security', name: 'Compliance & Security', icon: ShieldCheck },
  { path: '/license-risk', name: 'License Risk', icon: Key },
  { path: '/migration-advisor', name: 'Migration Advisor', icon: MessageSquare },
  { path: '/code-refactoring', name: 'Code Refactoring', icon: Code },
  { path: '/conversational-assistant', name: 'Conversational Assistant', icon: Bot },
  { path: '/agent-trace', name: 'Agent Trace', icon: Activity },
  { path: '/self-learning', name: 'Self-Learning', icon: BrainCircuit },
  { path: '/integrations', name: 'Integrations', icon: Cable },
  { path: '/stakeholder-comm', name: 'Stakeholder Comm', icon: Users },
];

export default function Layout() {
  const [isPinned, setIsPinned] = useState(true);
  const [isHovered, setIsHovered] = useState(false);

  const isExpanded = isPinned || isHovered;

  return (
    <>
      <div className="premium-bg"></div>
      <div className="grid-bg"></div>

      {/* Sidebar */}
      <aside 
        className={`glass-panel border-r flex flex-col h-full shrink-0 z-50 transition-all duration-300 ease-in-out absolute md:relative ${isExpanded ? 'w-72' : 'w-20'}`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
          <div className={`p-6 pb-6 flex items-center ${isExpanded ? 'justify-between' : 'justify-center'} gap-3`}>
              <div className="flex items-center gap-3 overflow-hidden">
                <div className="p-2 bg-indigo-500/10 rounded-lg border border-indigo-500/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] shrink-0">
                    <CloudLightning className="text-indigo-400 w-5 h-5" />
                </div>
                {isExpanded && <h1 className="text-2xl font-bold tracking-tight text-white drop-shadow-md whitespace-nowrap">D.A.M.I.</h1>}
              </div>
              
              {isExpanded && (
                <button 
                  onClick={() => setIsPinned(!isPinned)}
                  className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                >
                  {isPinned ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </button>
              )}
          </div>
          
          <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto overflow-x-hidden custom-scrollbar">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink 
                    key={item.path} 
                    to={item.path}
                    className={({ isActive }) => 
                      `flex items-center gap-3 px-3 py-3 rounded-xl transition-all relative overflow-hidden group ${
                        isActive 
                          ? 'bg-white/5 text-white border border-white/10 shadow-sm' 
                          : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                      }`
                    }
                    title={!isExpanded ? item.name : undefined}
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/5 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
                        )}
                        <div className="flex items-center justify-center shrink-0 w-6">
                            <Icon className={`w-5 h-5 relative z-10 ${isActive ? 'text-indigo-400' : ''}`} />
                        </div>
                        {isExpanded && (
                            <span className={`text-sm relative z-10 whitespace-nowrap ${isActive ? 'font-semibold' : 'font-medium'}`}>
                              {item.name}
                            </span>
                        )}
                      </>
                    )}
                  </NavLink>
                );
              })}
          </nav>
          
          <div className="p-4">
              <div className={`flex items-center ${isExpanded ? 'gap-3 px-4' : 'justify-center px-0'} py-3 rounded-xl bg-black/40 border border-white/5 overflow-hidden transition-all duration-300`}>
                  <div className="w-9 h-9 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4 text-slate-300" />
                  </div>
                  {isExpanded && (
                      <div className="flex flex-col whitespace-nowrap">
                          <span className="text-sm font-semibold text-white">Admin User</span>
                          <span className="text-xs text-slate-400 font-medium">FinOps Team</span>
                      </div>
                  )}
              </div>
          </div>
      </aside>

      {/* Main Content Rendered Here via React Router */}
      <div className={`flex-1 flex flex-col h-full overflow-hidden transition-all duration-300 ${!isExpanded ? 'ml-20 md:ml-0' : ''}`}>
        <Outlet />
      </div>
    </>
  );
}
