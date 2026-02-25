/* Milimo Quantum — Main App Component */
import { useState, useCallback } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { ChatArea } from './components/layout/ChatArea';
import { ArtifactPanel } from './components/layout/ArtifactPanel';
import { useChat } from './hooks/useChat';
import type { Artifact, AgentType } from './types';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);

  const {
    messages,
    isStreaming,
    activeAgent,
    setActiveAgent,
    sendMessage,
    clearChat,
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
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        activeAgent={activeAgent}
        onAgentSelect={handleAgentSelect}
        onNewChat={clearChat}
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
    </div>
  );
}

export default App;
