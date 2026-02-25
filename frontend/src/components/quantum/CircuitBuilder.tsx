/* Milimo Quantum — Visual Circuit Builder
 *
 * Drag-and-drop quantum gate palette. Users build circuits
 * by dragging gates onto qubit wires and can export to QASM.
 */
import { useState, useCallback, useRef } from 'react';
import { CircuitVisualizer } from './CircuitVisualizer';

/* ── Gate Palette ──────────────────────────────────────── */
const GATE_PALETTE = [
    { id: 'h', label: 'H', color: '#3ecfef', desc: 'Hadamard' },
    { id: 'x', label: 'X', color: '#c87070', desc: 'Pauli-X' },
    { id: 'y', label: 'Y', color: '#5cb8a0', desc: 'Pauli-Y' },
    { id: 'z', label: 'Z', color: '#c8a860', desc: 'Pauli-Z' },
    { id: 's', label: 'S', color: '#607890', desc: 'S gate' },
    { id: 't', label: 'T', color: '#88c8d8', desc: 'T gate' },
    { id: 'cx', label: 'CX', color: '#3ecfef', desc: 'CNOT' },
    { id: 'cz', label: 'CZ', color: '#c8a860', desc: 'CZ gate' },
    { id: 'swap', label: 'SW', color: '#607890', desc: 'SWAP' },
    { id: 'ccx', label: 'CCX', color: '#c8a860', desc: 'Toffoli' },
    { id: 'measure', label: 'M', color: '#a1a1aa', desc: 'Measure' },
] as const;

interface PlacedGate {
    id: string;
    gate: string;
    qubit: number;
    targetQubit?: number;
}

interface CircuitBuilderProps {
    onExport?: (code: string) => void;
}

export function CircuitBuilder({ onExport }: CircuitBuilderProps) {
    const [numQubits, setNumQubits] = useState(3);
    const [placedGates, setPlacedGates] = useState<PlacedGate[]>([]);
    const [dragGate, setDragGate] = useState<string | null>(null);
    const [showPreview, setShowPreview] = useState(false);
    const idCounter = useRef(0);

    const handleDragStart = useCallback((gateId: string) => {
        setDragGate(gateId);
    }, []);

    const handleDrop = useCallback((qubit: number) => {
        if (!dragGate) return;

        const newGate: PlacedGate = {
            id: `g${idCounter.current++}`,
            gate: dragGate,
            qubit,
        };

        // Two-qubit gates default target to next qubit
        if (['cx', 'cz', 'swap'].includes(dragGate)) {
            newGate.targetQubit = (qubit + 1) % numQubits;
        }
        if (dragGate === 'ccx') {
            newGate.targetQubit = Math.min(qubit + 2, numQubits - 1);
        }

        setPlacedGates(prev => [...prev, newGate]);
        setDragGate(null);
    }, [dragGate, numQubits]);

    const removeGate = useCallback((id: string) => {
        setPlacedGates(prev => prev.filter(g => g.id !== id));
    }, []);

    const clearAll = useCallback(() => {
        setPlacedGates([]);
    }, []);

    /* Generate Qiskit code from placed gates */
    const generateCode = useCallback(() => {
        const lines = [
            'from qiskit import QuantumCircuit',
            `qc = QuantumCircuit(${numQubits})`,
            '',
        ];

        for (const g of placedGates) {
            if (g.gate === 'measure') {
                lines.push('qc.measure_all()');
            } else if (['cx', 'cz', 'swap'].includes(g.gate) && g.targetQubit !== undefined) {
                lines.push(`qc.${g.gate}(${g.qubit}, ${g.targetQubit})`);
            } else if (g.gate === 'ccx' && g.targetQubit !== undefined) {
                const mid = Math.min(g.qubit + 1, numQubits - 1);
                lines.push(`qc.ccx(${g.qubit}, ${mid}, ${g.targetQubit})`);
            } else {
                lines.push(`qc.${g.gate}(${g.qubit})`);
            }
        }

        return lines.join('\n');
    }, [placedGates, numQubits]);

    const code = generateCode();

    return (
        <div className="space-y-4 animate-fade-in">
            {/* ── Gate Palette ──────────────────────────── */}
            <div>
                <label className="text-[10px] font-medium text-mq-text-tertiary uppercase tracking-wider mb-2 block">
                    Drag gates onto qubit wires
                </label>
                <div className="flex flex-wrap gap-1.5">
                    {GATE_PALETTE.map(g => (
                        <button
                            key={g.id}
                            draggable
                            onDragStart={() => handleDragStart(g.id)}
                            className="px-3 py-1.5 rounded-lg text-[11px] font-mono font-semibold
                                border cursor-grab active:cursor-grabbing transition-all
                                hover:brightness-125 hover:scale-105"
                            style={{
                                color: g.color,
                                borderColor: `${g.color}40`,
                                background: `${g.color}10`,
                            }}
                            title={g.desc}
                        >
                            {g.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* ── Qubit count + actions ─────────────────── */}
            <div className="flex items-center gap-3">
                <label className="text-xs text-mq-text-secondary">Qubits:</label>
                <input
                    type="range" min="1" max="8" value={numQubits}
                    onChange={e => setNumQubits(Number(e.target.value))}
                    className="w-24 accent-[#3ecfef]"
                />
                <span className="text-xs font-mono text-mq-cyan">{numQubits}</span>
                <div className="ml-auto flex gap-2">
                    <button
                        onClick={clearAll}
                        className="text-[10px] px-2 py-1 rounded-md border border-white/[0.06]
                            text-mq-text-tertiary hover:text-red-400 transition-colors cursor-pointer"
                    >Clear</button>
                    <button
                        onClick={() => setShowPreview(!showPreview)}
                        className="text-[10px] px-2 py-1 rounded-md border border-white/[0.06]
                            text-mq-text-tertiary hover:text-mq-cyan transition-colors cursor-pointer"
                    >{showPreview ? 'Hide Preview' : 'Show Preview'}</button>
                    <button
                        onClick={() => onExport?.(code)}
                        className="text-[10px] px-2 py-1 rounded-md border border-[#3ecfef]/20
                            text-mq-cyan hover:bg-[#3ecfef]/10 transition-colors cursor-pointer"
                    >Export Code</button>
                </div>
            </div>

            {/* ── Drop Target: Qubit Wires ─────────────── */}
            <div className="bg-black/40 border border-mq-border rounded-2xl p-4">
                {Array.from({ length: numQubits }, (_, q) => (
                    <div
                        key={q}
                        className="flex items-center gap-2 py-2 border-b border-white/[0.03] last:border-b-0"
                        onDragOver={e => e.preventDefault()}
                        onDrop={() => handleDrop(q)}
                    >
                        <span className="text-[11px] font-mono text-mq-text-tertiary w-8 shrink-0">
                            q{q}
                        </span>
                        <div className="flex-1 h-[1px] bg-white/[0.08] relative">
                            <div className="absolute inset-0 flex items-center gap-1">
                                {placedGates
                                    .filter(g => g.qubit === q)
                                    .map(g => {
                                        const palette = GATE_PALETTE.find(p => p.id === g.gate);
                                        return (
                                            <span
                                                key={g.id}
                                                onClick={() => removeGate(g.id)}
                                                className="inline-flex items-center justify-center w-7 h-7
                                                    rounded-md text-[10px] font-mono font-bold cursor-pointer
                                                    border hover:brightness-125 hover:scale-110 transition-all"
                                                style={{
                                                    color: palette?.color || '#a1a1aa',
                                                    borderColor: `${palette?.color || '#a1a1aa'}40`,
                                                    background: `${palette?.color || '#a1a1aa'}15`,
                                                }}
                                                title={`${palette?.desc || g.gate} — click to remove`}
                                            >
                                                {palette?.label || g.gate}
                                            </span>
                                        );
                                    })}
                            </div>
                        </div>
                    </div>
                ))}
                {placedGates.length === 0 && (
                    <p className="text-center text-[11px] text-mq-text-tertiary py-3">
                        Drag gates from the palette above onto any qubit wire
                    </p>
                )}
            </div>

            {/* ── Live Preview ──────────────────────────── */}
            {showPreview && (
                <div className="bg-black/30 border border-mq-border rounded-2xl p-4">
                    <p className="text-[10px] text-mq-text-tertiary uppercase tracking-wider mb-2 font-medium">
                        Live Preview
                    </p>
                    <CircuitVisualizer code={code} />
                </div>
            )}

            {/* ── Generated Code ───────────────────────── */}
            <div className="bg-black/50 border border-mq-border rounded-xl p-3">
                <p className="text-[10px] text-mq-text-tertiary uppercase tracking-wider mb-1.5 font-medium">
                    Generated Qiskit Code
                </p>
                <pre className="text-[11px] font-mono text-mq-cyan/80 whitespace-pre-wrap leading-relaxed">
                    {code}
                </pre>
            </div>
        </div>
    );
}
