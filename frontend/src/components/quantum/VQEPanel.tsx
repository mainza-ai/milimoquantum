import { useState, useRef, useEffect } from 'react';
import { runVQE, type VQERequest, type VQEResult } from '../../services/api';

interface VQEPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const HAMILTONIANS = [
  { value: 'h2', label: 'H₂ (Hydrogen)', qubits: 2 },
  { value: 'lih', label: 'LiH (Lithium Hydride)', qubits: 4 },
];

const ANSATZ_TYPES = [
  { value: 'efficient_su2', label: 'EfficientSU2' },
  { value: 'real_amplitudes', label: 'RealAmplitudes' },
  { value: 'two_local_ry_cz', label: 'TwoLocal (RY-CZ)' },
  { value: 'two_local_ryrz_cz', label: 'TwoLocal (RYRZ-CZ)' },
  { value: 'two_local_full', label: 'TwoLocal (Full)' },
];

const OPTIMIZERS = [
  { value: 'spsa', label: 'SPSA' },
  { value: 'cobyla', label: 'COBYLA' },
  { value: 'l_bfgs_b', label: 'L-BFGS-B' },
  { value: 'slsqp', label: 'SLSQP' },
];

export function VQEPanel({ isOpen, onClose }: VQEPanelProps) {
  const [hamiltonian, setHamiltonian] = useState('h2');
  const [ansatzType, setAnsatzType] = useState('real_amplitudes');
  const [ansatzReps, setAnsatzReps] = useState(2);
  const [optimizer, setOptimizer] = useState('spsa');
  const [maxIter, setMaxIter] = useState(100);
  const [seed, setSeed] = useState(42);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<VQEResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  if (!isOpen) return null;

  const handleRun = async () => {
    setIsRunning(true);
    setError(null);
    setResult(null);
    setLogs([`Starting VQE optimization for ${hamiltonian}...`]);

    const params: VQERequest = {
      hamiltonian,
      ansatz_type: ansatzType,
      ansatz_reps: ansatzReps,
      optimizer,
      optimizer_maxiter: maxIter,
      seed,
    };

    try {
      setLogs(prev => [...prev, `Config: ${ansatzType}, ${optimizer}, max_iter=${maxIter}`]);
      const res = await runVQE(params);
      setResult(res);
      setLogs(prev => [
        ...prev,
        `✅ Converged in ${res.iterations} iterations`,
        `Energy: ${res.eigenvalue.toFixed(6)} Ha`,
        res.reference_energy ? `Reference: ${res.reference_energy.toFixed(6)} Ha` : '',
        `Entanglement (Meyer-Wallach): ${res.circuit_stats.entanglement_score.toFixed(4)}`,
      ].filter(Boolean));
    } catch (e: any) {
      setError(e.message);
      setLogs(prev => [...prev, `❌ Error: ${e.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  // selectedH available for future use in showing qubit count

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#0d1117] border border-cyan-500/20 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden mx-4 flex flex-col">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-[#0d1117] border-b border-cyan-500/10 px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚛️</span>
            <div>
              <h2 className="text-lg font-semibold text-white">VQE Optimizer</h2>
              <p className="text-xs text-gray-400 mt-0.5">Variational Quantum Eigensolver with Qiskit Aer</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors text-xl">
            ✕
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Configuration Panel */}
          <div className="w-80 border-r border-cyan-500/10 p-6 overflow-y-auto">
            <h3 className="text-sm font-semibold text-cyan-400 mb-4 uppercase tracking-wider">Configuration</h3>

            {/* Hamiltonian */}
            <div className="mb-5">
              <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wider">Hamiltonian</label>
              <select
                value={hamiltonian}
                onChange={(e) => setHamiltonian(e.target.value)}
                disabled={isRunning}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
              >
                {HAMILTONIANS.map(h => (
                  <option key={h.value} value={h.value}>{h.label} ({h.qubits} qubits)</option>
                ))}
              </select>
            </div>

            {/* Ansatz */}
            <div className="mb-5">
              <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wider">Ansatz Circuit</label>
              <select
                value={ansatzType}
                onChange={(e) => setAnsatzType(e.target.value)}
                disabled={isRunning}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
              >
                {ANSATZ_TYPES.map(a => (
                  <option key={a.value} value={a.value}>{a.label}</option>
                ))}
              </select>
            </div>

            {/* Repetitions */}
            <div className="mb-5">
              <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wider">Repetitions (Depth)</label>
              <input
                type="number"
                min={1}
                max={10}
                value={ansatzReps}
                onChange={(e) => setAnsatzReps(parseInt(e.target.value) || 2)}
                disabled={isRunning}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Optimizer */}
            <div className="mb-5">
              <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wider">Optimizer</label>
              <select
                value={optimizer}
                onChange={(e) => setOptimizer(e.target.value)}
                disabled={isRunning}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
              >
                {OPTIMIZERS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            {/* Max Iterations */}
            <div className="mb-5">
              <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wider">Max Iterations</label>
              <input
                type="number"
                min={10}
                max={1000}
                value={maxIter}
                onChange={(e) => setMaxIter(parseInt(e.target.value) || 100)}
                disabled={isRunning}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Seed */}
            <div className="mb-6">
              <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wider">Random Seed</label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(parseInt(e.target.value) || 42)}
                disabled={isRunning}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Run Button */}
            <button
              onClick={handleRun}
              disabled={isRunning}
              className={`w-full py-3 rounded-xl text-sm font-bold transition-all ${
                isRunning
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-cyan-500 to-teal-500 text-black hover:brightness-110 shadow-lg shadow-cyan-500/25'
              }`}
            >
              {isRunning ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                  Optimizing...
                </span>
              ) : (
                '🚀 Run VQE'
              )}
            </button>
          </div>

          {/* Results Panel */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Log Console */}
            <div className="flex-1 bg-[#0a0a0f] p-4 overflow-y-auto font-mono text-sm">
              {logs.length === 0 && (
                <div className="h-full flex items-center justify-center text-gray-600">
                  <div className="text-center">
                    <div className="text-4xl mb-3 opacity-30">📊</div>
                    <p className="text-xs uppercase tracking-widest">Configure and run VQE to see results</p>
                  </div>
                </div>
              )}
              {logs.map((log, i) => (
                <div key={i} className="text-gray-300 mb-1">
                  <span className="text-gray-600 mr-3">{i + 1}</span>
                  {log}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>

            {/* Results Summary */}
            {result && (
              <div className="border-t border-cyan-500/10 p-4 bg-[#0d1117]">
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Ground State Energy</div>
                    <div className="text-lg font-bold text-cyan-400">{result.eigenvalue.toFixed(6)} Ha</div>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Reference</div>
                    <div className="text-lg font-bold text-white">
                      {result.reference_energy?.toFixed(6) || 'N/A'} Ha
                    </div>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Parameters</div>
                    <div className="text-lg font-bold text-white">{result.circuit_stats.num_params}</div>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Iterations</div>
                    <div className="text-lg font-bold text-white">{result.iterations}</div>
                  </div>
                </div>

                {/* Convergence Chart */}
                {result.convergence_trace.length > 0 && (
                  <div className="mt-4 bg-gray-800/30 rounded-lg p-3">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Convergence</div>
                    <div className="h-20 flex items-end gap-px">
                      {result.convergence_trace.filter((_, i) => i % Math.max(1, Math.floor(result.convergence_trace.length / 50)) === 0).map((point, i, arr) => {
                        const minE = Math.min(...arr.map(p => p.energy));
                        const maxE = Math.max(...arr.map(p => p.energy));
                        const range = maxE - minE || 1;
                        const height = ((point.energy - minE) / range) * 60 + 10;
                        return (
                          <div
                            key={i}
                            className="flex-1 bg-cyan-500/60 rounded-t"
                            style={{ height: `${height}%` }}
                            title={`Iter ${point.eval}: ${point.energy.toFixed(4)}`}
                          />
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="border-t border-red-500/20 p-4 bg-red-900/20">
                <div className="text-red-400 text-sm">❌ {error}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
