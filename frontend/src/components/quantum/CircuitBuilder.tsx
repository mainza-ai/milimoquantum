/* Milimo Quantum — Visual Circuit Builder
 *
 * Drag-and-drop quantum gate palette. Users build circuits
 * by dragging gates onto qubit wires and can export to QASM.
 */
import { useState, useCallback, useRef, useMemo } from 'react';
import { CircuitVisualizer } from './CircuitVisualizer';

/* ── Gate Palette ──────────────────────────────────────── */
const GATE_PALETTE = [
    { id: 'h', label: 'H', color: '#3ecfef', desc: 'Hadamard' },
    { id: 'x', label: 'X', color: '#c87070', desc: 'Pauli-X' },
    { id: 'y', label: 'Y', color: '#5cb8a0', desc: 'Pauli-Y' },
    { id: 'z', label: 'Z', color: '#c8a860', desc: 'Pauli-Z' },
    { id: 's', label: 'S', color: '#607890', desc: 'S gate' },
    { id: 't', label: 'T', color: '#88c8d8', desc: 'T gate' },
    { id: 'rx', label: 'Rx', color: '#e07848', desc: 'Rotation-X (θ)', parameterized: true },
    { id: 'ry', label: 'Ry', color: '#48b878', desc: 'Rotation-Y (θ)', parameterized: true },
    { id: 'rz', label: 'Rz', color: '#d8a838', desc: 'Rotation-Z (θ)', parameterized: true },
    { id: 'cx', label: 'CX', color: '#3ecfef', desc: 'CNOT' },
    { id: 'cz', label: 'CZ', color: '#c8a860', desc: 'CZ gate' },
    { id: 'swap', label: 'SW', color: '#607890', desc: 'SWAP' },
    { id: 'ccx', label: 'CCX', color: '#c8a860', desc: 'Toffoli' },
    { id: 'measure', label: 'M', color: '#a1a1aa', desc: 'Measure' },
] as const;

const PARAMETERIZED_GATES = new Set(['rx', 'ry', 'rz']);

interface PlacedGate {
    id: string;
    gate: string;
    qubit: number;
    targetQubit?: number;
    param?: number; // rotation angle in radians
}

interface CircuitBuilderProps {
    onExport?: (code: string) => void;
    onSendToChat?: (code: string) => void;
}

export function CircuitBuilder({ onExport, onSendToChat }: CircuitBuilderProps) {
    const [numQubits, setNumQubits] = useState(3);
    const [placedGates, setPlacedGates] = useState<PlacedGate[]>([]);
    const [dragGate, setDragGate] = useState<string | null>(null);
    const [showPreview, setShowPreview] = useState(false);
    const [simulating, setSimulating] = useState(false);
    const [simResult, setSimResult] = useState<string | null>(null);
    const [editingGate, setEditingGate] = useState<string | null>(null);
    const idCounter = useRef(0);

    // ── Undo / Redo ──────────────────────────────────────
    const historyRef = useRef<PlacedGate[][]>([[]]);
    const historyPosRef = useRef(0);

    const pushHistory = useCallback((newGates: PlacedGate[]) => {
        const pos = historyPosRef.current + 1;
        historyRef.current = historyRef.current.slice(0, pos);
        historyRef.current.push([...newGates]);
        historyPosRef.current = pos;
    }, []);

    const undo = useCallback(() => {
        if (historyPosRef.current <= 0) return;
        historyPosRef.current--;
        setPlacedGates([...historyRef.current[historyPosRef.current]]);
    }, []);

    const redo = useCallback(() => {
        if (historyPosRef.current >= historyRef.current.length - 1) return;
        historyPosRef.current++;
        setPlacedGates([...historyRef.current[historyPosRef.current]]);
    }, []);

    const canUndo = useMemo(() => historyPosRef.current > 0, [placedGates]);
    const canRedo = useMemo(() => historyPosRef.current < historyRef.current.length - 1, [placedGates]);

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
        // Parameterized gates default to π/2
        if (PARAMETERIZED_GATES.has(dragGate)) {
            newGate.param = Math.PI / 2;
        }

        const updated = [...placedGates, newGate];
        setPlacedGates(updated);
        pushHistory(updated);
        setDragGate(null);
    }, [dragGate, numQubits, placedGates, pushHistory]);

    const removeGate = useCallback((id: string) => {
        const updated = placedGates.filter(g => g.id !== id);
        setPlacedGates(updated);
        pushHistory(updated);
    }, [placedGates, pushHistory]);

    const updateGateParam = useCallback((id: string, param: number) => {
        const updated = placedGates.map(g => g.id === id ? { ...g, param } : g);
        setPlacedGates(updated);
        pushHistory(updated);
    }, [placedGates, pushHistory]);

    const clearAll = useCallback(() => {
        setPlacedGates([]);
        pushHistory([]);
    }, [pushHistory]);

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
            } else if (PARAMETERIZED_GATES.has(g.gate) && g.param !== undefined) {
                lines.push(`qc.${g.gate}(${g.param.toFixed(4)}, ${g.qubit})`);
            } else {
                lines.push(`qc.${g.gate}(${g.qubit})`);
            }
        }

        return lines.join('\n');
    }, [placedGates, numQubits]);

    /* Generate full runnable code with simulation */
    const generateRunnableCode = useCallback(() => {
        const hasMeasure = placedGates.some(g => g.gate === 'measure');
        const lines = [
            'from qiskit import QuantumCircuit, transpile',
            'from qiskit_aer import AerSimulator',
            '',
            `qc = QuantumCircuit(${numQubits})`,
            '',
        ];

        for (const g of placedGates) {
            if (g.gate === 'measure') {
                continue; // handled below
            } else if (['cx', 'cz', 'swap'].includes(g.gate) && g.targetQubit !== undefined) {
                lines.push(`qc.${g.gate}(${g.qubit}, ${g.targetQubit})`);
            } else if (g.gate === 'ccx' && g.targetQubit !== undefined) {
                const mid = Math.min(g.qubit + 1, numQubits - 1);
                lines.push(`qc.ccx(${g.qubit}, ${mid}, ${g.targetQubit})`);
            } else if (PARAMETERIZED_GATES.has(g.gate) && g.param !== undefined) {
                lines.push(`qc.${g.gate}(${g.param.toFixed(4)}, ${g.qubit})`);
            } else {
                lines.push(`qc.${g.gate}(${g.qubit})`);
            }
        }

        lines.push('');
        lines.push(hasMeasure ? 'qc.measure_all()' : 'qc.measure_all()');
        lines.push('');
        lines.push('sim = AerSimulator()');
        lines.push('transpiled = transpile(qc, sim)');
        lines.push('counts = sim.run(transpiled, shots=1024).result().get_counts()');
        lines.push('print(counts)');

        return lines.join('\n');
    }, [placedGates, numQubits]);

    /* Simulate the circuit via Celery job queue */
    const handleSimulate = useCallback(async () => {
        if (placedGates.length === 0) return;
        setSimulating(true);
        setSimResult(null);
        const runnableCode = generateRunnableCode();
        try {
            const res = await fetch('/api/jobs/execute-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: runnableCode }),
            });
            const data = await res.json();
            if (!data.job_id) {
                setSimResult(`❌ ${data.error || data.detail || 'Failed to queue'}`);
                setSimulating(false);
                return;
            }
            setSimResult('⏳ Queued for execution...');
            const pollInterval = setInterval(async () => {
                try {
                    const statusRes = await fetch(`/api/jobs/${data.job_id}/status`);
                    const statusData = await statusRes.json();
                    if (statusData.status === 'SUCCESS') {
                        clearInterval(pollInterval);
                        setSimulating(false);
                        const result = statusData.result;
                        if (result?.error) {
                            setSimResult(`❌ ${result.error}`);
                        } else {
                            setSimResult(`✅ ${result?.execution_time_ms || 0}ms` +
                                (result?.stdout ? `\n${result.stdout}` : ''));
                        }
                    } else if (statusData.status === 'FAILURE') {
                        clearInterval(pollInterval);
                        setSimulating(false);
                        setSimResult(`❌ ${statusData.error || 'Execution failed'}`);
                    } else {
                        setSimResult(`⏳ ${statusData.message || statusData.status}`);
                    }
                } catch {
                    clearInterval(pollInterval);
                    setSimulating(false);
                    setSimResult('❌ Polling failed');
                }
            }, 1000);
        } catch {
            setSimResult('❌ Connection failed');
            setSimulating(false);
        }
    }, [placedGates, generateRunnableCode]);

    /* Send circuit code to chat */
    const handleSendToChat = useCallback(() => {
        if (placedGates.length === 0) return;
        const runnableCode = generateRunnableCode();
        const chatMessage = `/code Run this circuit I built:\n\`\`\`python\n${runnableCode}\n\`\`\``;
        onSendToChat?.(chatMessage);
    }, [placedGates, generateRunnableCode, onSendToChat]);

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
                    <button onClick={undo} disabled={!canUndo}
                        className="text-[10px] px-2 py-1 rounded-md border border-white/[0.06]
                            text-mq-text-tertiary hover:text-mq-cyan transition-colors cursor-pointer
                            disabled:opacity-30 disabled:cursor-not-allowed"
                        title="Undo"
                    >↩</button>
                    <button onClick={redo} disabled={!canRedo}
                        className="text-[10px] px-2 py-1 rounded-md border border-white/[0.06]
                            text-mq-text-tertiary hover:text-mq-cyan transition-colors cursor-pointer
                            disabled:opacity-30 disabled:cursor-not-allowed"
                        title="Redo"
                    >↪</button>
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
                        onClick={handleSimulate}
                        disabled={simulating || placedGates.length === 0}
                        className={`text-[10px] px-2 py-1 rounded-md border transition-colors cursor-pointer
                            ${simulating
                                ? 'border-yellow-400/20 text-yellow-400 bg-yellow-400/10'
                                : 'border-green-400/20 text-green-400 hover:bg-green-400/10'
                            } disabled:opacity-40 disabled:cursor-not-allowed`}
                    >{simulating ? '⏳ Running...' : '▶ Simulate'}</button>
                    {onSendToChat && (
                        <button
                            onClick={handleSendToChat}
                            disabled={placedGates.length === 0}
                            className="text-[10px] px-2 py-1 rounded-md border border-[#3ecfef]/20
                                text-mq-cyan hover:bg-[#3ecfef]/10 transition-colors cursor-pointer
                                disabled:opacity-40 disabled:cursor-not-allowed"
                        >💬 Chat</button>
                    )}
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
                                        const isParam = PARAMETERIZED_GATES.has(g.gate);
                                        const isEditing = editingGate === g.id;
                                        return (
                                            <span key={g.id} className="relative inline-flex flex-col items-center">
                                                <span
                                                    onClick={() => {
                                                        if (isParam) {
                                                            setEditingGate(isEditing ? null : g.id);
                                                        } else {
                                                            removeGate(g.id);
                                                        }
                                                    }}
                                                    onContextMenu={(e) => { e.preventDefault(); removeGate(g.id); }}
                                                    className="inline-flex items-center justify-center w-7 h-7
                                                        rounded-md text-[10px] font-mono font-bold cursor-pointer
                                                        border hover:brightness-125 hover:scale-110 transition-all"
                                                    style={{
                                                        color: palette?.color || '#a1a1aa',
                                                        borderColor: `${palette?.color || '#a1a1aa'}40`,
                                                        background: `${palette?.color || '#a1a1aa'}15`,
                                                    }}
                                                    title={isParam
                                                        ? `${palette?.desc || g.gate} (θ=${((g.param ?? 0) / Math.PI).toFixed(2)}π) — click to edit, right-click to remove`
                                                        : `${palette?.desc || g.gate} — click to remove`}
                                                >
                                                    {palette?.label || g.gate}
                                                </span>
                                                {/* Parameter editing popover */}
                                                {isEditing && (
                                                    <div className="absolute top-8 left-1/2 -translate-x-1/2 z-20
                                                        bg-[#0d1117] border border-cyan-500/20 rounded-lg p-2.5
                                                        shadow-xl min-w-[140px] animate-fade-in"
                                                        onClick={e => e.stopPropagation()}
                                                    >
                                                        <div className="text-[9px] text-gray-500 mb-1">Angle (θ)</div>
                                                        <input
                                                            type="range"
                                                            min={0} max={6.2832} step={0.0001}
                                                            value={g.param ?? Math.PI / 2}
                                                            onChange={e => updateGateParam(g.id, Number(e.target.value))}
                                                            className="w-full accent-[#3ecfef] h-1.5"
                                                        />
                                                        <div className="text-[10px] font-mono text-mq-cyan text-center mt-1">
                                                            {((g.param ?? 0) / Math.PI).toFixed(3)}π
                                                            <span className="text-gray-600 ml-1">({(g.param ?? 0).toFixed(3)} rad)</span>
                                                        </div>
                                                        <button
                                                            onClick={() => removeGate(g.id)}
                                                            className="mt-1.5 w-full text-[9px] py-0.5 rounded text-red-400/70
                                                                hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                                                        >Remove Gate</button>
                                                    </div>
                                                )}
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

            {/* ── Simulation Result ──────────────────────── */}
            {simResult && (
                <pre className="bg-black/40 border border-mq-border rounded-xl p-3
                    text-[11px] font-mono text-mq-text-secondary whitespace-pre-wrap leading-relaxed animate-fade-in">
                    {simResult}
                </pre>
            )}
        </div>
    );
}
