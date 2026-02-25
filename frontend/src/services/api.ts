/* Milimo Quantum — API Service */

const API_BASE = '/api';

export async function fetchHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
}

export async function fetchQuantumStatus() {
    const res = await fetch(`${API_BASE}/quantum/status`);
    return res.json();
}

export async function fetchCircuits() {
    const res = await fetch(`${API_BASE}/quantum/circuits`);
    return res.json();
}

export async function executeCircuit(name: string, shots = 1024) {
    const res = await fetch(`${API_BASE}/quantum/execute/${name}?shots=${shots}`);
    return res.json();
}

// ── Fault Tolerance & Benchmarking ─────────────────────

export async function runBenchmark(name: string, size: number, shots = 1024) {
    const res = await fetch(`${API_BASE}/benchmarks/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, size, shots }),
    });
    return res.json();
}

export async function fetchBenchmarkHistory() {
    const res = await fetch(`${API_BASE}/benchmarks/history`);
    return res.json();
}

export async function fetchFaultTolerantResource(algo: string, size: number) {
    const res = await fetch(`${API_BASE}/quantum/ft/resource-estimation?algorithm=${algo}&size=${size}`);
    return res.json();
}

export async function fetchBibTeX(conversationId: string) {
    const res = await fetch(`${API_BASE}/citations/bibtex/${conversationId}`);
    return res.json();
}

// ── HPC & Marketplace ──────────────────────────────────

export async function fetchMarketplacePlugins() {
    const res = await fetch(`${API_BASE}/marketplace/`);
    return res.json();
}

export async function installPlugin(id: string) {
    const res = await fetch(`${API_BASE}/marketplace/install/${id}`, { method: 'POST' });
    return res.json();
}

export async function checkHpcStatus() {
    const res = await fetch(`${API_BASE}/hpc/status`);
    return res.json();
}

// ── Conversations ──────────────────────────────────────

export async function fetchConversations() {
    const res = await fetch(`${API_BASE}/chat/conversations`);
    return res.json();
}

export async function fetchConversation(id: string) {
    const res = await fetch(`${API_BASE}/chat/conversations/${id}`);
    return res.json();
}

export async function deleteConversation(id: string) {
    const res = await fetch(`${API_BASE}/chat/conversations/${id}`, { method: 'DELETE' });
    return res.json();
}

// ── Settings ───────────────────────────────────────────

export async function fetchSettings() {
    const res = await fetch(`${API_BASE}/settings/`);
    return res.json();
}

export async function fetchModels() {
    const res = await fetch(`${API_BASE}/settings/models`);
    return res.json();
}

export async function updateSettings(data: Record<string, unknown>) {
    const res = await fetch(`${API_BASE}/settings/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    return res.json();
}

// ── SSE Chat Stream ────────────────────────────────────

export function streamChat(
    message: string,
    conversationId?: string,
    agent?: string,
    onToken: (token: string) => void = () => { },
    onArtifact: (artifact: unknown) => void = () => { },
    onDone: (data: unknown) => void = () => { },
    onError: (error: string) => void = () => { },
) {
    const body = JSON.stringify({
        message,
        conversation_id: conversationId,
        agent: agent || null,
    });

    fetch(`${API_BASE}/chat/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
    })
        .then(async (response) => {
            if (!response.ok) {
                onError(`HTTP ${response.status}`);
                return;
            }
            const reader = response.body?.getReader();
            if (!reader) return;

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                let eventType = '';
                for (const line of lines) {
                    if (line.startsWith('event: ')) {
                        eventType = line.slice(7).trim();
                    } else if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        try {
                            const parsed = JSON.parse(data);
                            switch (eventType) {
                                case 'token':
                                    onToken(parsed.content || '');
                                    break;
                                case 'artifact':
                                    onArtifact(parsed);
                                    break;
                                case 'done':
                                    onDone(parsed);
                                    break;
                            }
                        } catch {
                            // ignore parse errors
                        }
                    }
                }
            }
        })
        .catch((err) => {
            onError(err.message || 'Connection failed');
        });
}

