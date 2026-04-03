/* Milimo Quantum — Main App Component */
import { useState, useCallback, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { ChatArea } from './components/layout/ChatArea';
import { ArtifactPanel } from './components/layout/ArtifactPanel';
import { WorkspaceManager } from './components/layout/WorkspaceManager';
import { useChat } from './hooks/useChat';
import type { Artifact, AgentType } from './types';
import { fetchCurrentUser, getStoredTokens, refreshAccessToken, setStoredTokens, clearStoredTokens } from './services/api';

const KEYCLOAK_URL = 'http://localhost:8081';
const REALM = 'milimo-realm';
const CLIENT_ID = 'milimo-client';
const REDIRECT_URI = 'http://localhost:5173/';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);

  useEffect(() => {
    const initAuth = async () => {
      const savedTheme = localStorage.getItem('mq-theme');
      if (savedTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
      }

      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');

      if (code) {
        window.history.replaceState(null, '', window.location.pathname);
        try {
          const tokenResponse = await fetch(`${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
              grant_type: 'authorization_code',
              client_id: CLIENT_ID,
              code: code,
              redirect_uri: REDIRECT_URI,
            }),
          });
          if (tokenResponse.ok) {
            const tokens = await tokenResponse.json();
            setStoredTokens(tokens.access_token, tokens.refresh_token);
            setIsAuthenticated(true);
            return;
          }
        } catch (e) {
          console.error('Token exchange failed:', e);
        }
      }

      const { accessToken, refreshToken } = getStoredTokens();
      if (accessToken) {
        try {
          await fetchCurrentUser();
          setIsAuthenticated(true);
        } catch (e: any) {
          if (e.message?.includes('401') && refreshToken) {
            try {
              const newAccessToken = await refreshAccessToken(refreshToken);
              localStorage.setItem('mq_token', newAccessToken);
              await fetchCurrentUser();
              setIsAuthenticated(true);
            } catch {
              clearStoredTokens();
              setIsAuthenticated(false);
            }
          } else {
            clearStoredTokens();
            setIsAuthenticated(false);
          }
        }
      } else {
        setIsAuthenticated(false);
      }
    };

    initAuth();
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
        onClick={() => window.location.href = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/auth?client_id=${CLIENT_ID}&response_type=code&redirect_uri=${encodeURIComponent(REDIRECT_URI)}`}
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

      {/* Dynamic Panel Manager */}
      <WorkspaceManager 
        currentConversationId={conversationId}
        loadConversation={loadConversation}
      />
    </div>
  );
}

export default App;
