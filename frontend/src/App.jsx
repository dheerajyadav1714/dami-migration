import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';

// Import Pages
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import IngestionCenter from './pages/IngestionCenter';
import ServerInventory from './pages/ServerInventory';
import DependencyMap from './pages/DependencyMap';
import RiskAssessment from './pages/RiskAssessment';
import MigrationWavePlan from './pages/MigrationWavePlan';
import TargetArchitecture from './pages/TargetArchitecture';
import IacAndRunbooks from './pages/IacAndRunbooks';
import FinopsAndTco from './pages/FinopsAndTco';
import ComplianceAndSecurity from './pages/ComplianceAndSecurity';
import LicenseRisk from './pages/LicenseRisk';
import Validation from './pages/Validation';
import MigrationAdvisor from './pages/MigrationAdvisor';
import CodeRefactoring from './pages/CodeRefactoring';
import CutoverSimulation from './pages/CutoverSimulation';
import Integrations from './pages/Integrations';
import StakeholderComm from './pages/StakeholderComm';
import AgentTrace from './pages/AgentTrace';
import SelfLearning from './pages/SelfLearning';
import ConversationalAssistant from './pages/ConversationalAssistant';
import ShadowItDetector from './pages/ShadowItDetector';
import VmwareLicenseShock from './pages/VmwareLicenseShock';
import CarbonFootprint from './pages/CarbonFootprint';
import QuotaPreChecker from './pages/QuotaPreChecker';
import BlackoutCalendar from './pages/BlackoutCalendar';
import DataSensitivity from './pages/DataSensitivity';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<ExecutiveDashboard />} />
          <Route path="ingestion-center" element={<IngestionCenter />} />
          <Route path="server-inventory" element={<ServerInventory />} />
          <Route path="dependency-map" element={<DependencyMap />} />
          <Route path="risk-assessment" element={<RiskAssessment />} />
          <Route path="migration-wave-plan" element={<MigrationWavePlan />} />
          <Route path="target-architecture" element={<TargetArchitecture />} />
          <Route path="iac-and-runbooks" element={<IacAndRunbooks />} />
          <Route path="finops-and-tco" element={<FinopsAndTco />} />
          <Route path="compliance-and-security" element={<ComplianceAndSecurity />} />
          <Route path="license-risk" element={<LicenseRisk />} />
          <Route path="validation" element={<Validation />} />
          <Route path="migration-advisor" element={<MigrationAdvisor />} />
          <Route path="code-refactoring" element={<CodeRefactoring />} />
          <Route path="cutover-simulation" element={<CutoverSimulation />} />
          <Route path="integrations" element={<Integrations />} />
          <Route path="stakeholder-comm" element={<StakeholderComm />} />
          <Route path="agent-trace" element={<AgentTrace />} />
          <Route path="self-learning" element={<SelfLearning />} />
          <Route path="conversational-assistant" element={<ConversationalAssistant />} />
          <Route path="shadow-it" element={<ShadowItDetector />} />
          <Route path="vmware-license" element={<VmwareLicenseShock />} />
          <Route path="carbon-footprint" element={<CarbonFootprint />} />
          <Route path="quota-checker" element={<QuotaPreChecker />} />
          <Route path="blackout-calendar" element={<BlackoutCalendar />} />
          <Route path="data-sensitivity" element={<DataSensitivity />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
