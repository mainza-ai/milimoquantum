/* Milimo Quantum — API Service */

const API_BASE = '/api';

export async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = localStorage.getItem('mq_token');
    const headers = new Headers(options.headers || {});

    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    // CSRF Protection Header
    const method = options.method?.toUpperCase() || 'GET';
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
        headers.set('X-Requested-With', 'XMLHttpRequest');
    }

    return fetch(url, { ...options, headers });
}

export async function fetchHealth() {
    const res = await fetchWithAuth(`${API_BASE}/health`);
    return res.json();
}

export async function fetchCurrentUser() {
    const res = await fetchWithAuth(`${API_BASE}/auth/me`);
    if (!res.ok) {
        throw new Error('Unauthorized');
    }
    return res.json();
}

export async function fetchQuantumStatus() {
    const res = await fetchWithAuth(`${API_BASE}/quantum/status`);
    return res.json();
}

export async function fetchCircuits() {
    const res = await fetchWithAuth(`${API_BASE}/quantum/circuits`);
    return res.json();
}

export async function executeCircuit(name: string, shots = 1024) {
    const res = await fetchWithAuth(`${API_BASE}/quantum/execute/${name}?shots=${shots}`);
    return res.json();
}

// ── Fault Tolerance & Benchmarking ─────────────────────

export async function runBenchmark(name: string, size: number, shots = 1024) {
    const res = await fetchWithAuth(`${API_BASE}/benchmarks/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, size, shots }),
    });
    return res.json();
}

export async function fetchBenchmarkHistory() {
    const res = await fetchWithAuth(`${API_BASE}/benchmarks/history`);
    return res.json();
}

export async function fetchFaultTolerantResource(algo: string, size: number) {
    const res = await fetchWithAuth(`${API_BASE}/quantum/ft/resource-estimation?algorithm=${algo}&size=${size}`);
    return res.json();
}

export async function fetchBibTeX(conversationId: string) {
    const res = await fetchWithAuth(`${API_BASE}/citations/bibtex/${conversationId}`);
    return res.json();
}

export async function fetchErrorMitigation(circuitName: string, method: string, shots: number = 4096) {
    const res = await fetchWithAuth(`${API_BASE}/quantum/mitigate/${circuitName}?method=${method}&shots=${shots}`, {
        method: 'POST'
    });
    return res.json();
}

export async function fetchQRNG(length: number = 256) {
    const res = await fetchWithAuth(`${API_BASE}/qrng/bits/${length}`);
    return res.json();
}

export async function fetchHardwareProviders() {
    const res = await fetchWithAuth(`${API_BASE}/quantum/providers`);
    return res.json();
}

// ── HPC & Marketplace ──────────────────────────────────

export async function fetchMarketplacePlugins() {
    const res = await fetchWithAuth(`${API_BASE}/marketplace/algorithms`);
    return res.json();
}

export async function installPlugin(id: string) {
    const res = await fetchWithAuth(`${API_BASE}/marketplace/install/${id}`, { method: 'POST' });
    return res.json();
}

export async function checkHpcStatus() {
    const res = await fetchWithAuth(`${API_BASE}/hpc/status`);
    return res.json();
}

// ── Conversations ──────────────────────────────────────

export async function fetchConversations(projectId?: string | null) {
    const params = projectId ? `?project_id=${projectId}` : '';
    const res = await fetchWithAuth(`${API_BASE}/chat/conversations${params}`);
    return res.json();
}

export async function fetchConversation(id: string) {
    const res = await fetchWithAuth(`${API_BASE}/chat/conversations/${id}`);
    return res.json();
}

export async function deleteConversation(id: string) {
    const res = await fetchWithAuth(`${API_BASE}/chat/conversations/${id}`, { method: 'DELETE' });
    return res.json();
}

// ── Settings ───────────────────────────────────────────

export async function fetchSettings() {
    const res = await fetchWithAuth(`${API_BASE}/settings/`);
    return res.json();
}

export async function fetchModels() {
    const res = await fetchWithAuth(`${API_BASE}/settings/models`);
    return res.json();
}

export async function updateSettings(data: Record<string, unknown>) {
    const res = await fetchWithAuth(`${API_BASE}/settings/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    return res.json();
}

// ── MLX Apple Silicon Providers ────────────────────────

export async function fetchMLXModels() {
    const res = await fetchWithAuth(`${API_BASE}/settings/mlx/models`);
    return res.json();
}

export async function searchMLXModels(query: string = "") {
    const res = await fetchWithAuth(`${API_BASE}/settings/mlx/search?q=${encodeURIComponent(query)}`);
    return res.json();
}

export async function pullMLXModel(modelId: string) {
    const res = await fetchWithAuth(`${API_BASE}/settings/mlx/pull`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelId }),
    });
    return res.json();
}

// ── SSE Chat Stream ────────────────────────────────────

// ── Cloud AI Providers ─────────────────────────────────

export async function fetchCloudProviders() {
    const res = await fetchWithAuth(`${API_BASE}/settings/cloud-providers`);
    return res.json();
}

export async function setCloudProvider(provider: string, model?: string, api_key?: string) {
    const res = await fetchWithAuth(`${API_BASE}/settings/cloud-provider`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, model, api_key }),
    });
    return res.json();
}

// ── Projects ───────────────────────────────────────────

export async function fetchProjects() {
    const res = await fetchWithAuth(`${API_BASE}/projects/`);
    return res.json();
}

export async function createProject(data: { name: string; description?: string; tags?: string[] }) {
    const res = await fetchWithAuth(`${API_BASE}/projects/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    return res.json();
}

export async function deleteProject(id: string) {
    const res = await fetchWithAuth(`${API_BASE}/projects/${id}`, { method: 'DELETE' });
    return res.json();
}

export async function addConversationToProject(projectId: string, conversationId: string) {
    const res = await fetchWithAuth(`${API_BASE}/projects/${projectId}/conversations/${conversationId}`, {
        method: 'POST',
    });
    return res.json();
}

// ── Dashboard ──────────────────────────────────────────

export async function fetchAnalyticsSummary() {
    const res = await fetchWithAuth(`${API_BASE}/analytics/summary`);
    return res.json();
}

export async function fetchCircuitStats() {
    const res = await fetchWithAuth(`${API_BASE}/analytics/circuits`);
    return res.json();
}

export async function fetchMLXPullStatus() {
    const res = await fetchWithAuth(`${API_BASE}/settings/mlx/pull/status`);
    return res.json();
}

export async function unloadMLXModel() {
    const res = await fetchWithAuth(`${API_BASE}/settings/mlx/unload`, { method: 'POST' });
    return res.json();
}

export async function fetchMLXConfig() {
    const res = await fetchWithAuth(`${API_BASE}/settings/mlx/config`);
    return res.json();
}

export async function updateMLXConfig(config: Record<string, unknown>) {
    const res = await fetchWithAuth(`${API_BASE}/settings/mlx/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });
    return res.json();
}

export function streamChat(
    message: string,
    conversationId?: string,
    agent?: string,
    fileId?: string,
    projectId?: string | null,
    onToken: (token: string) => void = () => { },
    onArtifact: (artifact: unknown) => void = () => { },
    onDone: (data: unknown) => void = () => { },
    onError: (error: string) => void = () => { },
) {
    const body = JSON.stringify({
        message,
        conversation_id: conversationId,
        project_id: projectId || null,
        agent: agent || null,
        attached_file_id: fileId || null,
    });

    fetchWithAuth(`${API_BASE}/chat/send`, {
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
                                case 'retry':
                                    // Auto-retry: show correction status in chat
                                    onToken(`\n\n🔄 *Auto-correcting code (attempt ${parsed.attempt}/${parsed.max})...*\n`);
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

// ── Graph Intelligence ─────────────────────────────────

export async function fetchGraphStatus() {
    const res = await fetchWithAuth(`${API_BASE}/graph/status`);
    return res.json();
}

export async function fetchGraphRelated(query: string) {
    const res = await fetchWithAuth(`${API_BASE}/graph/related?q=${encodeURIComponent(query)}`);
    return res.json();
}

export async function fetchGraphStats() {
    const res = await fetchWithAuth(`${API_BASE}/graph/stats`);
    return res.json();
}

export async function fetchAgentMemory(agentType: string, query?: string, projectId?: string | null) {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (projectId) params.append('project_id', projectId);
    
    const queryString = params.toString() ? `?${params.toString()}` : '';
    const res = await fetchWithAuth(`${API_BASE}/graph/memory/${agentType}${queryString}`);
    return res.json();
}

// ── Learning Academy ───────────────────────────────────

export async function fetchLessons() {
    const res = await fetchWithAuth(`${API_BASE}/academy/lessons`);
    return res.json();
}

export async function fetchLesson(id: string) {
    const res = await fetchWithAuth(`${API_BASE}/academy/lessons/${id}`);
    return res.json();
}

export async function saveAcademyProgress(lessonId: string, completed: boolean = true, quizScore?: number) {
    const params = new URLSearchParams({ lesson_id: lessonId, completed: String(completed) });
    if (quizScore !== undefined) params.set('quiz_score', String(quizScore));
    const res = await fetchWithAuth(`${API_BASE}/academy/progress?${params}`, { method: 'POST' });
    return res.json();
}

// ── Live Data Feeds ────────────────────────────────────

export async function searchArxivPapers(query: string, maxResults: number = 5) {
    const res = await fetchWithAuth(`${API_BASE}/feeds/arxiv?query=${encodeURIComponent(query)}&max_results=${maxResults}`);
    return res.json();
}

export async function searchPubChem(name: string) {
    const res = await fetchWithAuth(`${API_BASE}/feeds/pubchem?name=${encodeURIComponent(name)}`);
    return res.json();
}

export async function fetchStockPrices(symbols: string[]) {
  const res = await fetchWithAuth(`${API_BASE}/feeds/finance?symbols=${symbols.join(',')}`);
  return res.json();
}

// ── VQE (Variational Quantum Eigensolver) ───────────────

export interface VQERequest {
  hamiltonian?: string;
  hamiltonian_custom?: [string, number][];
  ansatz_type?: string;
  ansatz_reps?: number;
  optimizer?: string;
  optimizer_maxiter?: number;
  seed?: number;
}

export interface VQEResult {
  eigenvalue: number;
  reference_energy: number | null;
  optimal_point: number[];
  convergence_trace: { eval: number; energy: number }[];
  circuit_stats: {
    ansatz_type: string;
    depth: number;
    num_qubits: number;
    num_params: number;
    entanglement_score: number;
  };
  optimizer: string;
  iterations: number;
  seed: number;
  error?: string;
}

export async function runVQE(params: VQERequest): Promise<VQEResult> {
  const res = await fetchWithAuth(`${API_BASE}/autoresearch/vqe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'VQE execution failed');
  }
  return res.json();
}
