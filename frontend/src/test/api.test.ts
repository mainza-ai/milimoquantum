import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchWithAuth } from '../services/api';

// Mock fetch globally
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

describe('API Service', () => {
    beforeEach(() => {
        mockFetch.mockClear();
    });

    it('should have correct API base path', () => {
        // All API calls should go to /api/* prefix
        expect('/api/settings').toMatch(/^\/api\//);
        expect('/api/quantum/execute').toMatch(/^\/api\//);
        expect('/api/experiments/projects').toMatch(/^\/api\//);
    });

    it('fetchSettings should call correct endpoint', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ ollama_model: 'llama3.2', default_shots: 1024 }),
        });

        const response = await fetchWithAuth('/api/settings');
        const data = await response.json();

        expect(data.ollama_model).toBe('llama3.2');
        expect(data.default_shots).toBe(1024);
    });

    it('quantum execute should accept circuit code', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                status: 'success',
                counts: { '00': 512, '11': 512 },
            }),
        });

        const response = await fetchWithAuth('/api/quantum/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: 'qc = QuantumCircuit(2)\nqc.h(0)\nqc.cx(0,1)\nqc.measure_all()',
                shots: 1024,
            }),
        });
        const data = await response.json();

        expect(data.status).toBe('success');
        expect(data.counts).toHaveProperty('00');
        expect(data.counts).toHaveProperty('11');
    });

    it('cloud providers should return array', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                providers: [
                    { id: 'anthropic', name: 'Anthropic Claude', configured: false },
                    { id: 'openai', name: 'OpenAI', configured: false },
                    { id: 'gemini', name: 'Google Gemini', configured: false },
                    { id: 'cohere', name: 'Cohere Command R+', configured: false },
                    { id: 'mistral', name: 'Mistral AI', configured: false },
                    { id: 'deepseek', name: 'DeepSeek', configured: false },
                ],
            }),
        });

        const response = await fetchWithAuth('/api/settings/cloud-providers');
        const data = await response.json();

        expect(data.providers).toHaveLength(6);
        expect(data.providers.map((p: { id: string }) => p.id)).toContain('cohere');
        expect(data.providers.map((p: { id: string }) => p.id)).toContain('mistral');
        expect(data.providers.map((p: { id: string }) => p.id)).toContain('deepseek');
    });

    it('experiments endpoint should return projects', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                projects: [
                    { name: 'default', run_count: 5 },
                    { name: 'vqe_research', run_count: 12 },
                ],
            }),
        });

        const response = await fetchWithAuth('/api/experiments/projects');
        const data = await response.json();

        expect(data.projects).toBeInstanceOf(Array);
        expect(data.projects.length).toBeGreaterThanOrEqual(1);
    });

    it('citation export should return BibTeX', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                bibtex: '@article{grover1996,\n  title = {A Fast Quantum Mechanical Algorithm},\n}',
            }),
        });

        const response = await fetchWithAuth('/api/quantum/citations/bibtex', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ algorithms: ['grover'] }),
        });
        const data = await response.json();

        expect(data.bibtex).toContain('@article');
        expect(data.bibtex).toContain('grover');
    });
});
