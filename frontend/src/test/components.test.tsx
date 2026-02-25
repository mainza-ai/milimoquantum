/* Milimo Quantum — Component Rendering Tests */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageBubble } from '../components/chat/MessageBubble';
import type { ChatMessage } from '../types';

describe('MessageBubble', () => {
    it('renders user message correctly', () => {
        const msg: ChatMessage = {
            id: 'test-1',
            role: 'user',
            content: 'Create a Bell state circuit',
        };
        render(<MessageBubble message={msg} />);
        expect(screen.getByText('Create a Bell state circuit')).toBeInTheDocument();
    });

    it('renders assistant message with markdown', () => {
        const msg: ChatMessage = {
            id: 'test-2',
            role: 'assistant',
            content: 'Here is your **Bell state** circuit:',
            agent: 'code',
        };
        render(<MessageBubble message={msg} />);
        expect(screen.getByText(/Bell state/)).toBeInTheDocument();
    });

    it('renders code blocks in assistant messages', () => {
        const msg: ChatMessage = {
            id: 'test-3',
            role: 'assistant',
            content: '```python\nfrom qiskit import QuantumCircuit\n```',
            agent: 'code',
        };
        render(<MessageBubble message={msg} />);
        expect(screen.getByText(/QuantumCircuit/)).toBeInTheDocument();
    });

    it('renders LaTeX math expressions', () => {
        const msg: ChatMessage = {
            id: 'test-4',
            role: 'assistant',
            content: 'The state is $|\\psi\\rangle = \\frac{1}{\\sqrt{2}}(|00\\rangle + |11\\rangle)$',
            agent: 'research',
        };
        const { container } = render(<MessageBubble message={msg} />);
        // KaTeX renders .katex elements
        const katexElements = container.querySelectorAll('.katex');
        expect(katexElements.length).toBeGreaterThanOrEqual(1);
    });

    it('shows streaming cursor when isStreaming is true', () => {
        const msg: ChatMessage = {
            id: 'test-5',
            role: 'assistant',
            content: 'Processing...',
            agent: 'code',
            isStreaming: true,
        };
        const { container } = render(<MessageBubble message={msg} />);
        const cursor = container.querySelector('[style*="animation"]');
        expect(cursor).toBeInTheDocument();
    });

    it('renders artifact chips when artifacts exist', () => {
        const msg: ChatMessage = {
            id: 'test-6',
            role: 'assistant',
            content: 'Result:',
            agent: 'code',
            artifacts: [
                { id: '1', type: 'code', title: 'bell_state.py', content: '' },
                { id: '2', type: 'circuit', title: 'Circuit Diagram', content: '' },
            ],
        };
        render(<MessageBubble message={msg} />);
        expect(screen.getByText('bell_state.py')).toBeInTheDocument();
        expect(screen.getByText('Circuit Diagram')).toBeInTheDocument();
    });
});
