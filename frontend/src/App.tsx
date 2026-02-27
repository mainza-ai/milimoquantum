/* Milimo Quantum — Main App Component */
import { useState, useCallback, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { ChatArea } from './components/layout/ChatArea';
import { ArtifactPanel } from './components/layout/ArtifactPanel';
import SettingsPanel from './components/layout/SettingsPanel';
import { AnalyticsDashboard } from './components/layout/AnalyticsDashboard';
import { SearchPanel } from './components/layout/SearchPanel';
import { MarketplacePanel } from './components/layout/MarketplacePanel';
import { ProjectsPanel } from './components/layout/ProjectsPanel';
import { QuantumDashboard } from './components/layout/QuantumDashboard';
import { LearningAcademy } from './components/layout/LearningAcademy';
import { useChat } from './hooks/useChat';
import type { Artifact, AgentType } from './types';
import { fetchCurrentUser } from './services/api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [marketplaceOpen, setMarketplaceOpen] = useState(false);
  const [projectsOpen, setProjectsOpen] = useState(false);
  const [dashboardOpen, setDashboardOpen] = useState(false);
  const [academyOpen, setAcademyOpen] = useState(false);

  // Apply persisted theme on mount
  useEffect(() => {
    // Check URL hash for implicit token
    const hash = window.location.hash;
    if (hash && hash.includes('access_token=')) {
      const params = new URLSearchParams(hash.substring(1)); // remove #
      const token = params.get('access_token');
      if (token) {
        localStorage.setItem('mq_token', token);
        // Clear hash from URL
        window.history.replaceState(null, '', window.location.pathname + window.location.search);
      }
    }

    const saved = localStorage.getItem('mq-theme');
    if (saved === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    }

    fetchCurrentUser()
      .then(() => setIsAuthenticated(true))
      .catch(() => {
        localStorage.removeItem('mq_token');
        setIsAuthenticated(false)
      });
  }, []);

  const {
    messages,
    isStreaming,
    activeAgent,
    setActiveAgent,
    sendMessage,
    clearChat,
    loadConversation,
    conversationId,
  } = useChat();

  const handleArtifactClick = useCallback((artifact: Artifact) => {
    setActiveArtifact(artifact);
  }, []);

  const handleAgentSelect = useCallback(
    (agent: AgentType) => {
      setActiveAgent(agent);
    },
    [setActiveAgent],
  );

  if (isAuthenticated === null) {
    return (
      <div className="h-screen bg-[#0a0a0f] flex flex-col items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-quantum-cyan border-t-transparent animate-spin mb-4" />
        <p className="text-xs text-[#505060] tracking-[0.2em] uppercase">Authenticating</p>
      </div>
    );
  }

  if (isAuthenticated === false) {
    return (
      <div className="h-screen bg-[#0a0a0f] flex flex-col items-center justify-center relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-quantum-cyan/5 rounded-full blur-[100px] pointer-events-none" />

        <div className="z-10 flex flex-col items-center p-10 bg-[#18181f] border border-white/[0.08] rounded-2xl shadow-2xl w-full max-w-sm text-center">
          <img src="/logo_milimo.png" alt="Milimo Quantum" className="w-16 h-16 drop-shadow-[0_0_12px_rgba(62,207,239,0.3)] mb-6" />
          <h1 className="text-xl font-semibold text-[#e8e8ed] tracking-tight mb-2">Milimo Quantum</h1>
          <p className="text-[13px] text-[#8a8a9a] mb-8">Enterprise authentication required.</p>

          <button
            className="w-full bg-quantum-cyan text-black py-2.5 px-4 rounded-lg text-[13px] font-medium hover:bg-opacity-90 transition-all flex items-center justify-center gap-2 cursor-pointer"
            onClick={() => window.location.href = 'http://localhost:8080/realms/milimo-realm/protocol/openid-connect/auth?client_id=milimo-client&response_type=token&redirect_uri=http://localhost:5173/'}
          >
            Sign In with Keycloak
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex overflow-hidden">
      {/* Sidebar toggle (mobile) */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-3 left-3 z-50 lg:hidden w-9 h-9 rounded-lg
          bg-quantum-surface border border-quantum-border
          flex items-center justify-center text-quantum-text-dim
          hover:text-quantum-text hover:border-quantum-cyan/50
          transition-all cursor-pointer"
      >
        {sidebarOpen ? '✕' : '☰'}
      </button>

      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        activeAgent={activeAgent}
        onAgentSelect={handleAgentSelect}
        onNewChat={clearChat}
        onLoadConversation={loadConversation}
        onOpenSettings={() => setSettingsOpen(true)}
        onOpenAnalytics={() => setAnalyticsOpen(true)}
        onOpenSearch={() => setSearchOpen(true)}
        onOpenMarketplace={() => setMarketplaceOpen(true)}
        onOpenProjects={() => setProjectsOpen(true)}
        onOpenDashboard={() => setDashboardOpen(true)}
        onOpenAcademy={() => setAcademyOpen(true)}
        currentConversationId={conversationId}
      />

      {/* Chat Area */}
      <ChatArea
        messages={messages}
        isStreaming={isStreaming}
        activeAgent={activeAgent}
        onSend={sendMessage}
        onArtifactClick={handleArtifactClick}
      />

      {/* Artifact Panel */}
      <ArtifactPanel
        artifact={activeArtifact}
        onClose={() => setActiveArtifact(null)}
      />

      {/* Settings Modal */}
      <SettingsPanel
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />

      {/* Analytics Dashboard Modal */}
      <AnalyticsDashboard
        isOpen={analyticsOpen}
        onClose={() => setAnalyticsOpen(false)}
      />

      {/* Search Panel Modal */}
      <SearchPanel
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
        onLoadConversation={loadConversation}
      />

      {/* Marketplace Modal */}
      <MarketplacePanel
        isOpen={marketplaceOpen}
        onClose={() => setMarketplaceOpen(false)}
      />

      {/* Projects Modal */}
      <ProjectsPanel
        isOpen={projectsOpen}
        onClose={() => setProjectsOpen(false)}
        currentConversationId={conversationId}
      />

      {/* Quantum Dashboard Modal */}
      <QuantumDashboard
        isOpen={dashboardOpen}
        onClose={() => setDashboardOpen(false)}
      />

      {/* Learning Academy Modal */}
      <LearningAcademy
        isOpen={academyOpen}
        onClose={() => setAcademyOpen(false)}
      />
    </div>
  );
}

export default App;
