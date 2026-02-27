/* Milimo Quantum — Bloch Sphere Visualization
 *
 * SVG-based Bloch sphere that renders a qubit state vector
 * on the unit sphere using orthographic projection.
 * No Three.js dependency — pure SVG + CSS transforms.
 */
import { useMemo, useState } from 'react';

interface BlochSphereProps {
    /** Polar angle θ (theta) in radians [0, π] */
    theta?: number;
    /** Azimuthal angle φ (phi) in radians [0, 2π] */
    phi?: number;
    /** Size in pixels */
    size?: number;
    /** Label for the state */
    label?: string;
}

export function BlochSphere({
    theta = Math.PI / 4,
    phi = Math.PI / 6,
    size = 240,
    label,
}: BlochSphereProps) {
    const [hovered, setHovered] = useState(false);

    // Convert spherical → Cartesian
    const { x, y, z, projX, projY, alpha, beta } = useMemo(() => {
        const xVal = Math.sin(theta) * Math.cos(phi);
        const yVal = Math.sin(theta) * Math.sin(phi);
        const zVal = Math.cos(theta);

        // Oblique projection (cavalier) for nice 3D look
        const angle = Math.PI / 6; // 30° viewing angle
        const projXVal = xVal + 0.5 * yVal * Math.cos(angle);
        const projYVal = -zVal + 0.5 * yVal * Math.sin(angle);

        // State amplitudes
        const alphaVal = Math.cos(theta / 2);
        const betaVal = Math.sin(theta / 2);

        return {
            x: xVal,
            y: yVal,
            z: zVal,
            projX: projXVal,
            projY: projYVal,
            alpha: alphaVal,
            beta: betaVal,
        };
    }, [theta, phi]);

    const cx = size / 2;
    const cy = size / 2;
    const r = size * 0.36; // sphere radius in SVG
    const stateX = cx + projX * r;
    const stateY = cy + projY * r;

    // Axis endpoints in projected space
    const angle30 = Math.PI / 6;
    const xAxisEnd = { x: cx + r, y: cy };
    const yAxisEnd = { x: cx + 0.5 * r * Math.cos(angle30), y: cy + 0.5 * r * Math.sin(angle30) };
    const zAxisEnd = { x: cx, y: cy - r };

    return (
        <div
            className="relative inline-flex flex-col items-center"
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
        >
            <svg
                width={size}
                height={size}
                viewBox={`0 0 ${size} ${size}`}
                className="transition-transform duration-300"
                style={{ transform: hovered ? 'scale(1.05)' : 'scale(1)' }}
            >
                {/* Sphere outline */}
                <circle
                    cx={cx} cy={cy} r={r}
                    fill="none"
                    stroke="var(--color-mq-border-light)"
                    strokeWidth="1"
                    opacity="0.5"
                />

                {/* Equator ellipse */}
                <ellipse
                    cx={cx} cy={cy}
                    rx={r} ry={r * 0.3}
                    fill="none"
                    stroke="var(--color-mq-border-light)"
                    strokeWidth="0.5"
                    strokeDasharray="3,3"
                    opacity="0.3"
                />

                {/* Vertical meridian */}
                <ellipse
                    cx={cx} cy={cy}
                    rx={r * 0.3} ry={r}
                    fill="none"
                    stroke="var(--color-mq-border-light)"
                    strokeWidth="0.5"
                    strokeDasharray="3,3"
                    opacity="0.3"
                />

                {/* Axes */}
                {/* X axis */}
                <line
                    x1={cx - r * 0.3} y1={cy} x2={xAxisEnd.x} y2={xAxisEnd.y}
                    stroke="#c87070" strokeWidth="1" opacity="0.6"
                />
                <text x={xAxisEnd.x + 8} y={xAxisEnd.y + 4} fill="#c87070" fontSize="11" fontWeight="600">X</text>

                {/* Y axis */}
                <line
                    x1={cx - 0.3 * r * Math.cos(angle30)} y1={cy - 0.3 * r * Math.sin(angle30)}
                    x2={yAxisEnd.x} y2={yAxisEnd.y}
                    stroke="#5cb8a0" strokeWidth="1" opacity="0.6"
                />
                <text x={yAxisEnd.x + 8} y={yAxisEnd.y + 4} fill="#5cb8a0" fontSize="11" fontWeight="600">Y</text>

                {/* Z axis */}
                <line
                    x1={cx} y1={cy + r * 0.3} x2={zAxisEnd.x} y2={zAxisEnd.y}
                    stroke="#3ecfef" strokeWidth="1" opacity="0.6"
                />
                <text x={zAxisEnd.x + 6} y={zAxisEnd.y - 4} fill="#3ecfef" fontSize="11" fontWeight="600">Z</text>

                {/* Pole labels */}
                <text x={cx + 4} y={cy - r - 8} fill="#3ecfef" fontSize="12" fontWeight="600">|0⟩</text>
                <text x={cx + 4} y={cy + r + 16} fill="#c87070" fontSize="12" fontWeight="600">|1⟩</text>

                {/* State vector line */}
                <line
                    x1={cx} y1={cy} x2={stateX} y2={stateY}
                    stroke="#e879f9"
                    strokeWidth="2"
                    markerEnd="url(#arrowhead)"
                    className="transition-all duration-700 ease-in-out"
                />

                {/* State dot */}
                <circle cx={stateX} cy={stateY} r={5} fill="#e879f9" className="transition-all duration-700 ease-in-out" />
                <circle cx={stateX} cy={stateY} r={8} fill="#e879f9" opacity="0.2" className="transition-all duration-700 ease-in-out">
                    <animate attributeName="r" values="8;12;8" dur="2s" repeatCount="indefinite" />
                </circle>

                {/* Arrow marker */}
                <defs>
                    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                        <polygon points="0 0, 8 3, 0 6" fill="#e879f9" />
                    </marker>
                </defs>

                {/* Origin dot */}
                <circle cx={cx} cy={cy} r={2} fill="var(--color-mq-text-tertiary)" />
            </svg>

            {/* State info */}
            <div className="text-center mt-1 space-y-0.5">
                {label && (
                    <p className="text-xs font-medium text-mq-text">{label}</p>
                )}
                <p className="text-[10px] font-mono text-mq-text-tertiary">
                    |ψ⟩ = {alpha.toFixed(3)}|0⟩ + {beta.toFixed(3)}e<sup>i{(phi / Math.PI).toFixed(2)}π</sup>|1⟩
                </p>
                <p className="text-[10px] font-mono text-mq-text-tertiary">
                    θ = {(theta / Math.PI).toFixed(2)}π | φ = {(phi / Math.PI).toFixed(2)}π
                </p>
                <p className="text-[10px] font-mono text-[#636370]">
                    (x, y, z) = ({x.toFixed(2)}, {y.toFixed(2)}, {z.toFixed(2)})
                </p>
            </div>
        </div>
    );
}


/* ── Interactive Bloch Sphere with Controls ───────────── */
interface BlochSphereInteractiveProps {
    /** External theta from circuit results — overrides slider when set */
    externalTheta?: number;
    /** External phi from circuit results — overrides slider when set */
    externalPhi?: number;
    /** Label to show when external state is received */
    externalLabel?: string;
}

export function BlochSphereInteractive({ externalTheta, externalPhi, externalLabel }: BlochSphereInteractiveProps = {}) {
    const [theta, setTheta] = useState(externalTheta ?? Math.PI / 4);
    const [phi, setPhi] = useState(externalPhi ?? Math.PI / 6);
    const [isExternal, setIsExternal] = useState(false);

    // Auto-update when external state is received
    useMemo(() => {
        if (externalTheta !== undefined && externalPhi !== undefined) {
            setTheta(externalTheta);
            setPhi(externalPhi);
            setIsExternal(true);
        }
    }, [externalTheta, externalPhi]);

    // Preset states
    const presets = [
        { label: '|0⟩', theta: 0, phi: 0 },
        { label: '|1⟩', theta: Math.PI, phi: 0 },
        { label: '|+⟩', theta: Math.PI / 2, phi: 0 },
        { label: '|−⟩', theta: Math.PI / 2, phi: Math.PI },
        { label: '|i⟩', theta: Math.PI / 2, phi: Math.PI / 2 },
        { label: '|−i⟩', theta: Math.PI / 2, phi: 3 * Math.PI / 2 },
    ];

    const applyGate = (gate: string) => {
        // Current state in amplitudes: a|0> + b|1>
        const a_re = Math.cos(theta / 2);
        const a_im = 0;
        const b_re = Math.sin(theta / 2) * Math.cos(phi);
        const b_im = Math.sin(theta / 2) * Math.sin(phi);

        let n_a_re = a_re, n_a_im = a_im, n_b_re = b_re, n_b_im = b_im;

        if (gate === 'X') {
            n_a_re = b_re; n_a_im = b_im;
            n_b_re = a_re; n_b_im = a_im;
        } else if (gate === 'Y') {
            n_a_re = b_im; n_a_im = -b_re;
            n_b_re = -a_im; n_b_im = a_re;
        } else if (gate === 'Z') {
            n_a_re = a_re; n_a_im = a_im;
            n_b_re = -b_re; n_b_im = -b_im;
        } else if (gate === 'H') {
            const invSqrt2 = 1 / Math.sqrt(2);
            n_a_re = invSqrt2 * (a_re + b_re);
            n_a_im = invSqrt2 * (a_im + b_im);
            n_b_re = invSqrt2 * (a_re - b_re);
            n_b_im = invSqrt2 * (a_im - b_im);
        }

        // Convert back to spherical theta, phi
        const norm_a = Math.hypot(n_a_re, n_a_im);
        const newTheta = 2 * Math.acos(Math.min(1, Math.max(0, norm_a)));

        let newPhi = 0;
        if (newTheta > 1e-5 && newTheta < Math.PI - 1e-5) {
            const phase_a = Math.atan2(n_a_im, n_a_re);
            const phase_b = Math.atan2(n_b_im, n_b_re);
            newPhi = phase_b - phase_a;
        }

        while (newPhi < 0) newPhi += 2 * Math.PI;
        while (newPhi >= 2 * Math.PI) newPhi -= 2 * Math.PI;

        setTheta(newTheta);
        setPhi(newPhi);
        setIsExternal(false);
    };

    return (
        <div className="space-y-4">
            {/* External state indicator */}
            {isExternal && externalLabel && (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg
                    bg-purple-500/5 border border-purple-500/10 text-[10px]">
                    <span className="text-purple-400">🔗</span>
                    <span className="text-purple-300">{externalLabel}</span>
                    <button onClick={() => setIsExternal(false)}
                        className="ml-auto text-gray-500 hover:text-gray-300 cursor-pointer">✕</button>
                </div>
            )}

            {/* Controls Bar */}
            <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                    <span className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider">Gates</span>
                    <div className="flex gap-1.5">
                        {['X', 'Y', 'Z', 'H'].map(g => (
                            <button key={g} onClick={() => applyGate(g)}
                                className="w-7 h-7 rounded-lg text-xs font-mono font-bold
                                bg-cyan-500/10 text-cyan-400 border border-cyan-500/20
                                hover:bg-cyan-500/20 transition-all cursor-pointer shadow-sm
                                shadow-cyan-500/10 active:scale-95 flex items-center justify-center">
                                {g}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="flex items-center justify-between border-t border-white/[0.04] pt-2">
                    <span className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider">States</span>
                    <div className="flex flex-wrap justify-end gap-1.5">
                        {presets.map(p => (
                            <button
                                key={p.label}
                                onClick={() => { setTheta(p.theta); setPhi(p.phi); setIsExternal(false); }}
                                className="px-2 py-1 rounded bg-white/[0.02] border border-white/[0.06]
                                text-[10px] font-mono font-semibold text-gray-400
                                hover:text-white hover:border-gray-500 transition-all cursor-pointer"
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <BlochSphere theta={theta} phi={phi} label={isExternal ? externalLabel : undefined} />

            {/* Sliders */}
            <div className="space-y-2">
                <div className="flex items-center gap-3">
                    <label className="text-[10px] text-mq-text-tertiary w-6">θ</label>
                    <input
                        type="range" min="0" max={Math.PI} step="0.01"
                        value={theta}
                        onChange={e => { setTheta(Number(e.target.value)); setIsExternal(false); }}
                        className="flex-1 accent-[#e879f9]"
                    />
                    <span className="text-[10px] font-mono text-mq-text-tertiary w-14 text-right">
                        {(theta / Math.PI).toFixed(2)}π
                    </span>
                </div>
                <div className="flex items-center gap-3">
                    <label className="text-[10px] text-mq-text-tertiary w-6">φ</label>
                    <input
                        type="range" min="0" max={2 * Math.PI} step="0.01"
                        value={phi}
                        onChange={e => { setPhi(Number(e.target.value)); setIsExternal(false); }}
                        className="flex-1 accent-[#e879f9]"
                    />
                    <span className="text-[10px] font-mono text-mq-text-tertiary w-14 text-right">
                        {(phi / Math.PI).toFixed(2)}π
                    </span>
                </div>
            </div>
        </div>
    );
}
