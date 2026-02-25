/* Milimo Quantum — TypeScript Type Definitions */

export type AgentType = 'orchestrator' | 'code' | 'research' | 'chemistry' | 'finance' | 'optimization' | 'crypto' | 'qml' | 'climate';

export type ArtifactType = 'code' | 'circuit' | 'results' | 'notebook' | 'report';

export interface Artifact {
    id: string;
    type: ArtifactType;
    title: string;
    content: string;
    language?: string;
    metadata?: Record<string, unknown>;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    agent?: AgentType;
    artifacts?: Artifact[];
    timestamp?: string;
    isStreaming?: boolean;
}

export interface Conversation {
    id: string;
    title: string;
    messages: ChatMessage[];
    createdAt?: string;
}

export interface PlatformInfo {
    os: string;
    arch: string;
    torch_device: string;
    aer_device: string;
    llm_backend: string;
    gpu_available: boolean;
    gpu_name?: string;
}

export interface HealthStatus {
    status: string;
    ollama: string;
    qiskit: string;
}

export interface AgentInfo {
    type: AgentType;
    name: string;
    icon: string;
    color: string;
    command: string;
    description: string;
}

export const AGENTS: AgentInfo[] = [
    {
        type: 'orchestrator',
        name: 'Milimo',
        icon: '⚛',
        color: '#3ecfef',
        command: '',
        description: 'General quantum AI assistant',
    },
    {
        type: 'code',
        name: 'Code Agent',
        icon: '💻',
        color: '#5bb8d4',
        command: '/code',
        description: 'Qiskit code generation & circuits',
    },
    {
        type: 'research',
        name: 'Research',
        icon: '📚',
        color: '#88c8d8',
        command: '/research',
        description: 'Quantum concepts & education',
    },
    {
        type: 'chemistry',
        name: 'Chemistry',
        icon: '🧪',
        color: '#70b8cc',
        command: '/chemistry',
        description: 'Molecular simulation & drug discovery',
    },
    {
        type: 'finance',
        name: 'Finance',
        icon: '📈',
        color: '#a0d0e0',
        command: '/finance',
        description: 'Portfolio optimization & risk',
    },
    {
        type: 'optimization',
        name: 'Optimize',
        icon: '⚡',
        color: '#c0dce6',
        command: '/optimize',
        description: 'QAOA, VQE, combinatorial problems',
    },
    {
        type: 'crypto',
        name: 'Crypto',
        icon: '🔐',
        color: '#d4a0e0',
        command: '/crypto',
        description: 'QKD, post-quantum security, QRNG',
    },
    {
        type: 'qml',
        name: 'Quantum ML',
        icon: '🧠',
        color: '#e0c080',
        command: '/qml',
        description: 'QNN, QSVM, quantum kernels',
    },
    {
        type: 'climate',
        name: 'Climate',
        icon: '🌍',
        color: '#80d0a0',
        command: '/climate',
        description: 'Materials, batteries, climate models',
    },
];
