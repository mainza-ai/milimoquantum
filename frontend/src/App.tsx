/* Milimo Quantum — Main App Component */
import { useState, useCallback } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { ChatArea } from './components/layout/ChatArea';
import { ArtifactPanel } from './components/layout/ArtifactPanel';
import SettingsPanel from './components/layout/SettingsPanel';
import { AnalyticsDashboard } from './components/layout/AnalyticsDashboard';
import { SearchPanel } from './components/layout/SearchPanel';
import { MarketplacePanel } from './components/layout/MarketplacePanel';
import { useChat } from './hooks/useChat';
import type { Artifact, AgentType } from './types';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [marketplaceOpen, setMarketplaceOpen] = useState(false);

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
      />

      {/* Marketplace Modal */}
      <MarketplacePanel
        isOpen={marketplaceOpen}
        onClose={() => setMarketplaceOpen(false)}
      />
    </div>
  );
}

export default App;

