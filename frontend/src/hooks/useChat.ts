/* Milimo Quantum — Chat Hook */
import { useState, useCallback, useRef } from 'react';
import { streamChat, fetchConversation } from '../services/api';
import type { ChatMessage, Artifact, AgentType } from '../types';

let msgCounter = 0;

export function useChat() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [artifacts, setArtifacts] = useState<Artifact[]>([]);
    const [conversationId, setConversationId] = useState<string | undefined>();
    const [activeAgent, setActiveAgent] = useState<AgentType>('orchestrator');
    const streamingRef = useRef('');

    const sendMessage = useCallback(
        (content: string) => {
            if (!content.trim() || isStreaming) return;

            // Detect agent from slash command
            let agent: string | undefined;
            const slashMatch = content.match(/^\/(code|research|chemistry|finance|optimize)\b/);
            if (slashMatch) {
                agent = slashMatch[1] === 'optimize' ? 'optimization' : slashMatch[1];
                setActiveAgent(agent as AgentType);
            }

            // Add user message
            const userMsg: ChatMessage = {
                id: `msg-${++msgCounter}`,
                role: 'user',
                content,
            };
            setMessages((prev) => [...prev, userMsg]);

            // Add placeholder assistant message
            const assistantId = `msg-${++msgCounter}`;
            const assistantMsg: ChatMessage = {
                id: assistantId,
                role: 'assistant',
                content: '',
                isStreaming: true,
                agent: (agent as AgentType) || activeAgent,
            };
            setMessages((prev) => [...prev, assistantMsg]);
            setIsStreaming(true);
            streamingRef.current = '';

            streamChat(
                content,
                conversationId,
                agent,
                // onToken
                (token: string) => {
                    streamingRef.current += token;
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId
                                ? { ...m, content: streamingRef.current }
                                : m,
                        ),
                    );
                },
                // onArtifact
                (artifact: unknown) => {
                    const a = artifact as Artifact;
                    setArtifacts((prev) => [...prev, a]);
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId
                                ? {
                                    ...m,
                                    artifacts: [...(m.artifacts || []), a],
                                }
                                : m,
                        ),
                    );
                },
                // onDone
                (data: unknown) => {
                    const d = data as { conversation_id?: string; agent?: string };
                    if (d.conversation_id) setConversationId(d.conversation_id);
                    if (d.agent) setActiveAgent(d.agent as AgentType);
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId ? { ...m, isStreaming: false } : m,
                        ),
                    );
                    setIsStreaming(false);
                },
                // onError
                (error: string) => {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId
                                ? {
                                    ...m,
                                    content: `⚠️ ${error}\n\nMake sure the backend is running: \`cd backend && python run.py\``,
                                    isStreaming: false,
                                }
                                : m,
                        ),
                    );
                    setIsStreaming(false);
                },
            );
        },
        [isStreaming, conversationId, activeAgent],
    );

    const clearChat = useCallback(() => {
        setMessages([]);
        setArtifacts([]);
        setConversationId(undefined);
    }, []);

    const loadConversation = useCallback(async (id: string) => {
        try {
            const data = await fetchConversation(id);
            if (data.messages && data.messages.length > 0) {
                const loaded: ChatMessage[] = data.messages.map((m: { role: string; content: string }) => ({
                    id: `loaded-${++msgCounter}`,
                    role: m.role as 'user' | 'assistant',
                    content: m.content,
                }));
                setMessages(loaded);
                setConversationId(id);
                setArtifacts([]);
            }
        } catch {
            // silently fail
        }
    }, []);

    return {
        messages,
        isStreaming,
        artifacts,
        activeAgent,
        setActiveAgent,
        sendMessage,
        clearChat,
        loadConversation,
        conversationId,
    };
}
