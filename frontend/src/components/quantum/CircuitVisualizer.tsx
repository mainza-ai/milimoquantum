/* Milimo Quantum — Interactive Circuit Visualizer
 *
 * Parses QASM-style circuit descriptions and renders them as
 * interactive SVG diagrams with hover tooltips.
 */
import { useState, useMemo, useRef, useCallback } from 'react';

/* ── Gate metadata ─────────────────────────────────────── */
const GATE_INFO: Record<string, { label: string; color: string; desc: string }> = {
    h: { label: 'H', color: '#3ecfef', desc: 'Hadamard — creates superposition' },
    x: { label: 'X', color: '#c87070', desc: 'Pauli-X — bit flip (NOT gate)' },
    y: { label: 'Y', color: '#5cb8a0', desc: 'Pauli-Y — bit + phase flip' },
    z: { label: 'Z', color: '#c8a860', desc: 'Pauli-Z — phase flip' },
    s: { label: 'S', color: '#607890', desc: 'S gate — π/2 phase rotation' },
    t: { label: 'T', color: '#88c8d8', desc: 'T gate — π/4 phase rotation' },
    rx: { label: 'Rx', color: '#c87070', desc: 'Rotation around X-axis' },
    ry: { label: 'Ry', color: '#5cb8a0', desc: 'Rotation around Y-axis' },
    rz: { label: 'Rz', color: '#c8a860', desc: 'Rotation around Z-axis' },
    cx: { label: 'CX', color: '#3ecfef', desc: 'CNOT — controlled X (entanglement)' },
    cnot: { label: 'CX', color: '#3ecfef', desc: 'CNOT — controlled X (entanglement)' },
    swap: { label: 'SW', color: '#607890', desc: 'SWAP — exchange qubit states' },
    ccx: { label: 'CCX', color: '#c8a860', desc: 'Toffoli — controlled-controlled X' },
    measure: { label: 'M', color: '#a1a1aa', desc: 'Measurement — collapses qubit to |0⟩ or |1⟩' },
};

interface Gate {
    name: string;
    qubits: number[];
    col: number;
}

interface TooltipState {
    x: number;
    y: number;
    gate: Gate;
}

/* ── Simple QASM / code parser ─────────────────────────── */
function parseCircuit(code: string): { numQubits: number; gates: Gate[] } {
    const gates: Gate[] = [];
    let numQubits = 2;
    let col = 0;

    const lines = code.split('\n');
    for (const line of lines) {
        const trimmed = line.trim();

        // QuantumCircuit(n) → detect qubit count
        const qcMatch = trimmed.match(/QuantumCircuit\s*\(\s*(\d+)/);
        if (qcMatch) {
            numQubits = parseInt(qcMatch[1], 10);
            continue;
        }

        // qreg q[n] → detect qubit count
        const qregMatch = trimmed.match(/qreg\s+\w+\[(\d+)\]/);
        if (qregMatch) {
            numQubits = Math.max(numQubits, parseInt(qregMatch[1], 10));
            continue;
        }

        // qc.h(0), qc.cx(0, 1), qc.measure_all(), etc.
        const gateMatch = trimmed.match(/(?:qc|circuit|q)\.\s*(\w+)\s*\(\s*([\d,\s]*)\)/);
        if (gateMatch) {
            const gateName = gateMatch[1].toLowerCase();
            const args = gateMatch[2]
                .split(',')
                .map(s => s.trim())
                .filter(s => s.length > 0)
                .map(Number)
                .filter(n => !isNaN(n));

            if (gateName === 'measure_all') {
                for (let i = 0; i < numQubits; i++) {
                    gates.push({ name: 'measure', qubits: [i], col });
                }
                col++;
            } else if (GATE_INFO[gateName] || gateName === 'measure') {
                gates.push({ name: gateName, qubits: args.length > 0 ? args : [0], col });
                col++;
            }
            continue;
        }

        // QASM: h q[0]; cx q[0],q[1];
        const qasmMatch = trimmed.match(/^(\w+)\s+(q\[\d+\](?:\s*,\s*q\[\d+\])*)/);
        if (qasmMatch) {
            const gateName = qasmMatch[1].toLowerCase();
            const qubits = [...qasmMatch[2].matchAll(/q\[(\d+)\]/g)].map(m => parseInt(m[1], 10));
            if (GATE_INFO[gateName] || gateName === 'measure') {
                gates.push({ name: gateName, qubits, col });
                col++;
            }
        }
    }

    return { numQubits: Math.max(numQubits, 2), gates };
}

/* ── SVG constants ─────────────────────────────────────── */
const WIRE_Y_START = 40;
const WIRE_SPACING = 50;
const GATE_WIDTH = 36;
const COL_WIDTH = 52;
const LABEL_WIDTH = 40;

interface CircuitVisualizerProps {
    code: string;
    simulating?: boolean;
}

export function CircuitVisualizer({ code, simulating = false }: CircuitVisualizerProps) {
    const [tooltip, setTooltip] = useState<TooltipState | null>(null);
    const { numQubits, gates } = useMemo(() => parseCircuit(code), [code]);

    if (gates.length === 0) {
        return (
            <div className="text-center text-mq-text-tertiary text-sm py-8">
                No circuit gates detected. Try writing a Qiskit circuit or QASM code.
            </div>
        );
    }

    const maxCol = Math.max(...gates.map(g => g.col), 0);
    const svgWidth = LABEL_WIDTH + (maxCol + 2) * COL_WIDTH;
    const svgHeight = WIRE_Y_START + numQubits * WIRE_SPACING + 20;

    const wireY = (qubit: number) => WIRE_Y_START + qubit * WIRE_SPACING;
    const gateX = (col: number) => LABEL_WIDTH + (col + 0.5) * COL_WIDTH;

    // ── Zoom / Pan state ─────────────────────────────────
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const isPanning = useRef(false);
    const lastMouse = useRef({ x: 0, y: 0 });

    const handleWheel = useCallback((e: React.WheelEvent) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        setZoom(prev => Math.max(0.3, Math.min(3, prev * delta)));
    }, []);

    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        if (e.button === 0) {
            isPanning.current = true;
            lastMouse.current = { x: e.clientX, y: e.clientY };
        }
    }, []);

    const handleMouseMove = useCallback((e: React.MouseEvent) => {
        if (!isPanning.current) return;
        const dx = e.clientX - lastMouse.current.x;
        const dy = e.clientY - lastMouse.current.y;
        lastMouse.current = { x: e.clientX, y: e.clientY };
        setPan(prev => ({ x: prev.x + dx, y: prev.y + dy }));
    }, []);

    const handleMouseUp = useCallback(() => {
        isPanning.current = false;
    }, []);

    const resetView = useCallback(() => {
        setZoom(1);
        setPan({ x: 0, y: 0 });
    }, []);

    return (
        <div className="relative">
            {/* Zoom controls */}
            <div className="absolute top-2 right-2 z-10 flex gap-1">
                <button onClick={() => setZoom(z => Math.min(3, z * 1.2))}
                    className="w-6 h-6 rounded bg-white/[0.06] border border-white/[0.08]
                        text-xs text-gray-400 hover:text-white hover:bg-white/[0.1]
                        flex items-center justify-center transition-all cursor-pointer"
                >+</button>
                <button onClick={() => setZoom(z => Math.max(0.3, z * 0.8))}
                    className="w-6 h-6 rounded bg-white/[0.06] border border-white/[0.08]
                        text-xs text-gray-400 hover:text-white hover:bg-white/[0.1]
                        flex items-center justify-center transition-all cursor-pointer"
                >−</button>
                <button onClick={resetView}
                    className="px-1.5 h-6 rounded bg-white/[0.06] border border-white/[0.08]
                        text-[9px] text-gray-400 hover:text-white hover:bg-white/[0.1]
                        flex items-center justify-center transition-all cursor-pointer"
                >{Math.round(zoom * 100)}%</button>
            </div>

            <div
                className="overflow-hidden rounded-lg cursor-grab active:cursor-grabbing"
                onWheel={handleWheel}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
            >
                <svg
                    width={svgWidth}
                    height={svgHeight}
                    viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                    className="w-full h-auto"
                    style={{
                        maxWidth: `${svgWidth}px`,
                        transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
                        transformOrigin: 'top left',
                        transition: isPanning.current ? 'none' : 'transform 0.1s ease-out',
                    }}
                >
                    {/* Qubit labels */}
                    {Array.from({ length: numQubits }, (_, i) => (
                        <text
                            key={`label-${i}`}
                            x={8}
                            y={wireY(i) + 4}
                            fill="var(--color-mq-text-tertiary)"
                            fontSize="11"
                            fontFamily="var(--font-mono)"
                        >
                            q{i}
                        </text>
                    ))}

                    {/* Qubit wires */}
                    {Array.from({ length: numQubits }, (_, i) => (
                        <line
                            key={`wire-${i}`}
                            x1={LABEL_WIDTH}
                            y1={wireY(i)}
                            x2={svgWidth - 10}
                            y2={wireY(i)}
                            stroke={simulating ? "var(--color-mq-cyan)" : "var(--color-mq-border-light)"}
                            strokeWidth="1.5"
                            className={simulating ? "animate-pulse" : ""}
                        />
                    ))}

                    {/* Gates */}
                    {gates.map((gate, idx) => {
                        const info = GATE_INFO[gate.name] || { label: gate.name, color: '#636370', desc: '' };
                        const x = gateX(gate.col);

                        // CNOT: draw dot on control, ⊕ on target
                        if ((gate.name === 'cx' || gate.name === 'cnot') && gate.qubits.length >= 2) {
                            const [control, target] = gate.qubits;
                            return (
                                <g
                                    key={idx}
                                    onMouseEnter={(e) => setTooltip({ x: e.clientX, y: e.clientY, gate })}
                                    onMouseLeave={() => setTooltip(null)}
                                    style={{ cursor: 'pointer' }}
                                    className={simulating ? "animate-pulse" : ""}
                                >
                                    {/* Vertical line between control and target */}
                                    <line
                                        x1={x} y1={wireY(control)}
                                        x2={x} y2={wireY(target)}
                                        stroke={info.color} strokeWidth="2"
                                    />
                                    {/* Control dot */}
                                    <circle cx={x} cy={wireY(control)} r={5} fill={info.color} />
                                    {/* Target ⊕ */}
                                    <circle cx={x} cy={wireY(target)} r={12} fill="none" stroke={info.color} strokeWidth="2" />
                                    <line x1={x - 8} y1={wireY(target)} x2={x + 8} y2={wireY(target)} stroke={info.color} strokeWidth="2" />
                                    <line x1={x} y1={wireY(target) - 8} x2={x} y2={wireY(target) + 8} stroke={info.color} strokeWidth="2" />
                                </g>
                            );
                        }

                        // SWAP: two X marks connected by a vertical line
                        if (gate.name === 'swap' && gate.qubits.length >= 2) {
                            const [q0, q1] = gate.qubits;
                            return (
                                <g
                                    key={idx}
                                    onMouseEnter={(e) => setTooltip({ x: e.clientX, y: e.clientY, gate })}
                                    onMouseLeave={() => setTooltip(null)}
                                    style={{ cursor: 'pointer' }}
                                    className={simulating ? "animate-pulse" : ""}
                                >
                                    <line x1={x} y1={wireY(q0)} x2={x} y2={wireY(q1)} stroke={info.color} strokeWidth="2" />
                                    {/* X on q0 */}
                                    <line x1={x - 6} y1={wireY(q0) - 6} x2={x + 6} y2={wireY(q0) + 6} stroke={info.color} strokeWidth="2" />
                                    <line x1={x + 6} y1={wireY(q0) - 6} x2={x - 6} y2={wireY(q0) + 6} stroke={info.color} strokeWidth="2" />
                                    {/* X on q1 */}
                                    <line x1={x - 6} y1={wireY(q1) - 6} x2={x + 6} y2={wireY(q1) + 6} stroke={info.color} strokeWidth="2" />
                                    <line x1={x + 6} y1={wireY(q1) - 6} x2={x - 6} y2={wireY(q1) + 6} stroke={info.color} strokeWidth="2" />
                                </g>
                            );
                        }

                        // CCX (Toffoli): two control dots + target ⊕
                        if (gate.name === 'ccx' && gate.qubits.length >= 3) {
                            const [c0, c1, target] = gate.qubits;
                            const minY = Math.min(wireY(c0), wireY(c1), wireY(target));
                            const maxY = Math.max(wireY(c0), wireY(c1), wireY(target));
                            return (
                                <g
                                    key={idx}
                                    onMouseEnter={(e) => setTooltip({ x: e.clientX, y: e.clientY, gate })}
                                    onMouseLeave={() => setTooltip(null)}
                                    style={{ cursor: 'pointer' }}
                                    className={simulating ? "animate-pulse" : ""}
                                >
                                    <line x1={x} y1={minY} x2={x} y2={maxY} stroke={info.color} strokeWidth="2" />
                                    <circle cx={x} cy={wireY(c0)} r={5} fill={info.color} />
                                    <circle cx={x} cy={wireY(c1)} r={5} fill={info.color} />
                                    <circle cx={x} cy={wireY(target)} r={12} fill="none" stroke={info.color} strokeWidth="2" />
                                    <line x1={x - 8} y1={wireY(target)} x2={x + 8} y2={wireY(target)} stroke={info.color} strokeWidth="2" />
                                    <line x1={x} y1={wireY(target) - 8} x2={x} y2={wireY(target) + 8} stroke={info.color} strokeWidth="2" />
                                </g>
                            );
                        }

                        // CZ: two dots connected by a line
                        if (gate.name === 'cz' && gate.qubits.length >= 2) {
                            const [q0, q1] = gate.qubits;
                            return (
                                <g
                                    key={idx}
                                    onMouseEnter={(e) => setTooltip({ x: e.clientX, y: e.clientY, gate })}
                                    onMouseLeave={() => setTooltip(null)}
                                    style={{ cursor: 'pointer' }}
                                    className={simulating ? "animate-pulse" : ""}
                                >
                                    <line x1={x} y1={wireY(q0)} x2={x} y2={wireY(q1)} stroke={info.color} strokeWidth="2" />
                                    <circle cx={x} cy={wireY(q0)} r={5} fill={info.color} />
                                    <circle cx={x} cy={wireY(q1)} r={5} fill={info.color} />
                                </g>
                            );
                        }

                        // Measurement: meter icon
                        if (gate.name === 'measure') {
                            const y = wireY(gate.qubits[0]);
                            return (
                                <g
                                    key={idx}
                                    onMouseEnter={(e) => setTooltip({ x: e.clientX, y: e.clientY, gate })}
                                    onMouseLeave={() => setTooltip(null)}
                                    style={{ cursor: 'pointer' }}
                                    className={simulating ? "animate-pulse" : ""}
                                >
                                    <rect
                                        x={x - GATE_WIDTH / 2} y={y - 16}
                                        width={GATE_WIDTH} height={32}
                                        rx={4}
                                        fill="rgba(161,161,170,0.1)"
                                        stroke={info.color}
                                        strokeWidth="1.5"
                                    />
                                    {/* Meter arc */}
                                    <path
                                        d={`M ${x - 8} ${y + 4} A 8 8 0 0 1 ${x + 8} ${y + 4}`}
                                        fill="none" stroke={info.color} strokeWidth="1.5"
                                    />
                                    {/* Meter needle */}
                                    <line x1={x} y1={y + 4} x2={x + 6} y2={y - 8} stroke={info.color} strokeWidth="1.5" />
                                </g>
                            );
                        }

                        // Standard single-qubit gate box
                        const y = wireY(gate.qubits[0]);
                        return (
                            <g
                                key={idx}
                                onMouseEnter={(e) => setTooltip({ x: e.clientX, y: e.clientY, gate })}
                                onMouseLeave={() => setTooltip(null)}
                                style={{ cursor: 'pointer' }}
                                className={simulating ? "animate-pulse" : ""}
                            >
                                <rect
                                    x={x - GATE_WIDTH / 2} y={y - 16}
                                    width={GATE_WIDTH} height={32}
                                    rx={6}
                                    fill={`${info.color}15`}
                                    stroke={info.color}
                                    strokeWidth="1.5"
                                />
                                <text
                                    x={x} y={y + 4}
                                    textAnchor="middle"
                                    fill={info.color}
                                    fontSize="12"
                                    fontWeight="600"
                                    fontFamily="var(--font-mono)"
                                >
                                    {info.label}
                                </text>
                            </g>
                        );
                    })}
                </svg>
            </div>

            {/* Tooltip */}
            {tooltip && (
                <div
                    className="fixed z-50 px-3 py-2 rounded-xl glass-strong text-xs animate-fade-in"
                    style={{
                        left: tooltip.x + 12,
                        top: tooltip.y - 40,
                        pointerEvents: 'none',
                    }}
                >
                    <div className="font-semibold text-mq-text">
                        {GATE_INFO[tooltip.gate.name]?.label || tooltip.gate.name}
                    </div>
                    <div className="text-mq-text-tertiary mt-0.5">
                        {GATE_INFO[tooltip.gate.name]?.desc || 'Quantum gate'}
                    </div>
                    <div className="text-mq-cyan mt-0.5 font-mono">
                        qubits: [{tooltip.gate.qubits.join(', ')}]
                    </div>
                </div>
            )}
        </div>
    );
}
