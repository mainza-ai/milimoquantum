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
