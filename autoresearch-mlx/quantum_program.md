# Quantum Autoresearch Program

## Goal
Minimize `val_energy` (ground state energy in Hartree) using VQE simulation.
The H₂ molecule exact ground state energy is **-1.85728 Ha**.

## Rules (same as upstream autoresearch)
- Budget: 5-minute wall-clock per experiment
- Mutable file: `vqe_train.py` (or the CONFIG block in `autoresearch_mlx/vqe_train.py`)
- Metric: `val_energy` — lower is better
- Commit if val_energy strictly improves. Revert if not.
- One change per experiment. Do not combine multiple changes.

## What you can change (in CONFIG block only)

### ansatz_type
- `efficient_su2` — Hardware-efficient ansatz. Good general baseline.
- `real_amplitudes` — Fewer parameters. Faster, less expressive.
- `two_local_ry_cz` — Linear entanglement. Low depth.
- `two_local_ryrz_cz` — More rotations. Higher expressibility.

### ansatz_reps
- Range: 1–4
- Higher reps = deeper circuit, more parameters, more expressive, slower
- Start: try halving or doubling from current value

### optimizer
- `spsa` — Stochastic. Works well for noisy landscapes. High iteration count.
- `cobyla` — Derivative-free. Fast convergence on smooth landscapes.
- `l_bfgs_b` — Quasi-Newton. Excellent for smooth problems.
- `slsqp` — Constrained. Good with bounded parameters.

### optimizer_maxiter
- Range: 50–500
- More iterations → better convergence but slower

## Entanglement constraint
val_energy = +inf if Meyer-Wallach score < 0.3.
This prevents the agent from converging to separable (non-quantum) circuits.

## Results log
See `results_quantum.tsv` for history.

## Starting baseline
```
ansatz_type=real_amplitudes
reps=2
optimizer=spsa
maxiter=300
```
Baseline val_energy: ~-1.84 Ha (target: -1.85728 Ha)

## Key insight from MLX autoresearch experiments
In a fixed time budget, fewer parameters + more optimizer iterations often
beats more parameters + fewer iterations. Try reducing reps before adding
new optimizer iterations.

## API Integration

The VQE endpoint is available at:
```
POST /api/autoresearch/vqe
Content-Type: application/json

{
  "hamiltonian": "h2",
  "ansatz_type": "real_amplitudes",
  "ansatz_reps": 2,
  "optimizer": "cobyla",
  "optimizer_maxiter": 100
}
```

## Local Execution

From the autoresearch-mlx directory:
```bash
python -c "
from autoresearch_mlx.vqe_runner import run_vqe_local
result = run_vqe_local(
    hamiltonian='h2',
    ansatz_type='real_amplitudes',
    optimizer='cobyla',
    optimizer_maxiter=100
)
print(f'Energy: {result[\"eigenvalue\"]:.6f} Ha')
print(f'Reference: {result[\"reference_energy\"]:.6f} Ha')
print(f'Error: {result[\"error_from_reference\"]:.6f} Ha')
"
```

## Hamiltonian Presets

| Name | Qubits | Reference Energy | Description |
|------|--------|------------------|-------------|
| h2 | 2 | -1.85728 Ha | Hydrogen molecule |
| lih | 4 | -7.882 Ha | Lithium hydride |

## Meyer-Wallach Entanglement Score

The MW score measures global entanglement in [0, 1]:
- 0.0: Fully separable (no entanglement)
- 1.0: Maximally entangled (Bell states, GHZ states)

For VQE, we want MW > 0.3 to ensure the ansatz can represent entangled ground states.
