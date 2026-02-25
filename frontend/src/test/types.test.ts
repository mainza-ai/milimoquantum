/* Milimo Quantum — Types & Agents Tests */
import { describe, it, expect } from 'vitest';
import { AGENTS } from '../types';
import type { ChatMessage, Artifact } from '../types';

describe('AGENTS constant', () => {
    it('should have at least 10 agents defined', () => {
        expect(AGENTS.length).toBeGreaterThanOrEqual(10);
    });

    it('every agent should have required fields', () => {
        for (const agent of AGENTS) {
            expect(agent).toHaveProperty('type');
            expect(agent).toHaveProperty('name');
            expect(agent).toHaveProperty('icon');
            expect(agent).toHaveProperty('color');
            expect(agent).toHaveProperty('description');
            expect(agent).toHaveProperty('command');
        }
    });

    it('agent types should be unique', () => {
        const types = AGENTS.map(a => a.type);
        expect(new Set(types).size).toBe(types.length);
    });

    it('agent commands should be unique (excluding empty)', () => {
        const commands = AGENTS.filter(a => a.command).map(a => a.command);
        expect(new Set(commands).size).toBe(commands.length);
    });

    it('all agents except orchestrator should have slash commands', () => {
        const nonOrchestrator = AGENTS.filter(a => a.type !== 'orchestrator');
        for (const agent of nonOrchestrator) {
            expect(agent.command).toBeTruthy();
            expect(agent.command).toMatch(/^\//);
        }
    });

    it('should include key domain agents', () => {
        const types = AGENTS.map(a => a.type);
        expect(types).toContain('code');
        expect(types).toContain('research');
        expect(types).toContain('chemistry');
        expect(types).toContain('finance');
        expect(types).toContain('optimization');
        expect(types).toContain('crypto');
        expect(types).toContain('qml');
        expect(types).toContain('climate');
    });
});

describe('Type structures', () => {
    it('ChatMessage type should accept valid messages', () => {
        const msg: ChatMessage = {
            id: 'test-msg-1',
            role: 'user',
            content: 'Create a Bell state',
        };
        expect(msg.role).toBe('user');
        expect(msg.content).toBeTruthy();
    });

    it('Artifact type should accept valid artifacts', () => {
        const artifact: Artifact = {
            id: 'test-1',
            type: 'code',
            title: 'Bell State',
            content: 'from qiskit import QuantumCircuit',
        };
        expect(artifact.id).toBeTruthy();
        expect(artifact.type).toBe('code');
    });
});
