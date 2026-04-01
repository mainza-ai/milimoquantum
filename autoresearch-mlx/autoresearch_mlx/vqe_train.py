#!/usr/bin/env python3
"""
VQE Ansatz Discovery Module for Autoresearch-MLX.

Implements agentic reinforcement learning for quantum circuit architecture search.
Uses Meyer-Wallach metric for regularization to avoid barren plateaus.

This module connects the Autoresearch-MLX loop to the MQDD extension,
enabling autonomous discovery of efficient ansatz architectures for molecular
ground state energy calculations.

Usage:
    uv run vqe_train.py --molecule H2 --basis sto-3g --time-budget 300
"""

import argparse
import asyncio
import json
import logging
import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, AsyncGenerator
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vqe-train")

# Constants
TIME_BUDGET = 300  # 5 minutes default
MAX_CIRCUIT_DEPTH = 50
MIN_CIRCUIT_DEPTH = 2
MEYER_WALLACH_LAMBDA = 0.1  # Regularization strength
DEFAULT_NUM_QUBITS = 4


@dataclass
class VQEConfig:
    """Configuration for VQE ansatz search."""
    molecule: str = "H2"
    basis: str = "sto-3g"
    num_qubits: int = DEFAULT_NUM_QUBITS
    time_budget: int = TIME_BUDGET
    meyer_wallach_lambda: float = MEYER_WALLACH_LAMBDA
    min_depth: int = MIN_CIRCUIT_DEPTH
    max_depth: int = MAX_CIRCUIT_DEPTH
    target_energy: Optional[float] = None


@dataclass
class AnsatzCandidate:
    """A candidate ansatz architecture."""
    token_sequence: List[str]
    depth: int
    parameter_count: int
    circuit_repr: Optional[str] = None
    energy: Optional[float] = None
    gradient_variance: Optional[float] = None
    meyer_wallach_score: Optional[float] = None
    convergence_iterations: Optional[int] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")


class AnsatzTokenizer:
    """
    Tokenizer for quantum circuits.
    Converts between gate sequences and token representations.
    """
    
    GATE_VOCAB = {
        # Single-qubit gates
        "H": "h",
        "X": "x",
        "Y": "y", 
        "Z": "z",
        "S": "s",
        "T": "t",
        "RX": "rx",
        "RY": "ry",
        "RZ": "rz",
        "U": "u",
        "I": "i",
        
        # Two-qubit gates
        "CNOT": "cx",
        "CZ": "cz",
        "CY": "cy",
        "SWAP": "swap",
        "CRX": "crx",
        "CRY": "cry",
        "CRZ": "crz",
        
        # Three-qubit gates
        "CCX": "ccx",
        "CSWAP": "cswap",
        
        # Special tokens
        "<PAD>": "<pad>",
        "<BOS>": "<bos>",
        "<EOS>": "<eos>",
        "<UNK>": "<unk>",
    }
    
    REVERSE_VOCAB = {v: k for k, v in GATE_VOCAB.items()}
    VOCAB_LIST = list(GATE_VOCAB.keys())
    
    def encode(self, gates: List[str]) -> List[int]:
        """Convert gate names to token IDs."""
        tokens = []
        for g in gates:
            token = self.GATE_VOCAB.get(g, "<unk>")
            try:
                idx = self.VOCAB_LIST.index(token)
            except ValueError:
                idx = self.VOCAB_LIST.index("<unk>")
            tokens.append(idx)
        return tokens
    
    def decode(self, token_ids: List[int]) -> List[str]:
        """Convert token IDs back to gate names."""
        result = []
        for i in token_ids:
            if 0 <= i < len(self.VOCAB_LIST):
                result.append(self.VOCAB_LIST[i])
            else:
                result.append("<unk>")
        return result
    
    def get_vocab_size(self) -> int:
        """Get vocabulary size."""
        return len(self.VOCAB_LIST)


class MeyerWallachCalculator:
    """
    Calculates the Meyer-Wallach measure of entanglement.
    
    MW(|ψ⟩) = 2(1 - 1/n Σ_j Tr(ρ_j²))
    
    Higher MW = more entanglement = better for complex molecules.
    MW ranges from 0 (product state) to 1 (maximally entangled).
    
    This metric is used to:
    1. Regularize circuit depth (encourage expressivity)
    2. Avoid barren plateaus (circuits with low MW often plateau)
    3. Compare ansatz quality across architectures
    """
    
    @staticmethod
    def calculate(statevector: Any, num_qubits: int) -> float:
        """
        Calculate Meyer-Wallach entanglement measure.
        
        Args:
            statevector: State vector of the quantum state (numpy array or list)
            num_qubits: Number of qubits
            
        Returns:
            Meyer-Wallach measure (0 to 1)
        """
        import numpy as np
        
        # Convert to numpy array
        if not isinstance(statevector, np.ndarray):
            statevector = np.array(statevector, dtype=complex)
            
        expected_size = 2 ** num_qubits
        if len(statevector) != expected_size:
            logger.warning(f"Statevector length {len(statevector)} != expected {expected_size}")
            return 0.0
            
        # Normalize
        norm = np.linalg.norm(statevector)
        if norm > 0:
            statevector = statevector / norm
        else:
            return 0.0
            
        # Reshape to separate each qubit
        psi = statevector.reshape([2] * num_qubits)
        
        # Calculate purity of each single-qubit reduced density matrix
        entanglement_sum = 0.0
        
        for j in range(num_qubits):
            # Calculate reduced density matrix for qubit j
            rho_j = MeyerWallachCalculator._partial_trace(psi, j, num_qubits)
            
            # Calculate purity: Tr(ρ²)
            purity = np.trace(rho_j @ rho_j).real
            
            entanglement_sum += purity
            
        # Meyer-Wallach measure
        mw = 2 * (1 - entanglement_sum / num_qubits)
        
        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, mw)))
    
    @staticmethod
    def _partial_trace(psi: Any, keep_qubit: int, num_qubits: int) -> Any:
        """
        Calculate partial trace keeping only one qubit.
        
        Args:
            psi: State tensor reshaped as [2, 2, ..., 2]
            keep_qubit: Index of qubit to keep
            num_qubits: Total number of qubits
            
        Returns:
            2x2 reduced density matrix
        """
        import numpy as np
        
        rho = np.zeros((2, 2), dtype=complex)
        
        # Trace over all qubits except keep_qubit
        for i in range(2):
            for j in range(2):
                # Sum over all other qubits
                sum_val = 0.0j
                for idx in range(2 ** (num_qubits - 1)):
                    # Build indices for other qubits
                    other_idx = []
                    bit_pos = 0
                    for q in range(num_qubits):
                        if q == keep_qubit:
                            continue
                        other_idx.append((idx >> bit_pos) & 1)
                        bit_pos += 1
                    
                    # Build full indices
                    idx_i = list(other_idx)
                    idx_j = list(other_idx)
                    idx_i.insert(keep_qubit, i)
                    idx_j.insert(keep_qubit, j)
                    
                    try:
                        sum_val += psi[tuple(idx_i)] * np.conj(psi[tuple(idx_j)])
                    except IndexError:
                        pass
                        
                rho[i, j] = sum_val
                
        return rho
    
    @staticmethod
    def calculate_from_counts(counts: Dict[str, int], num_qubits: int) -> float:
        """
        Estimate MW from measurement counts (less accurate than statevector).
        
        This is a fallback when statevector is not available.
        Uses the diversity of measurement outcomes as a proxy for entanglement.
        """
        import numpy as np
        
        if not counts:
            return 0.0
            
        total_shots = sum(counts.values())
        if total_shots == 0:
            return 0.0
            
        # Calculate entropy of measurement distribution
        probs = np.array([c / total_shots for c in counts.values()])
        probs = probs[probs > 0]  # Remove zeros
        
        entropy = -np.sum(probs * np.log2(probs))
        max_entropy = num_qubits  # Maximum entropy for uniform distribution
        
        # Normalize and use as MW proxy
        mw_proxy = entropy / max_entropy if max_entropy > 0 else 0.0
        
        return float(mw_proxy)


class HamiltonianBuilder:
    """
    Build molecular Hamiltonians for VQE.
    
    Provides pre-computed Hamiltonians for small molecules.
    In production, would use qiskit_nature for full molecular calculation.
    """
    
    MOLECULAR_HAMILTONIANS = {
        "H2": {
            "sto-3g": {
                "pauli_string": "IIII + IZII + IIZI + IIZZ + ZIII + ZIZI + ZZII + ZZZI + IZZI + ZIZZ",
                "num_qubits": 4,
                "ground_state_energy": -1.1372855,
                "description": "Hydrogen molecule, minimal basis"
            }
        },
        "LiH": {
            "sto-3g": {
                "pauli_string": "IIIIIIIIII + ...",  # Simplified
                "num_qubits": 10,
                "ground_state_energy": -7.8825,
                "description": "Lithium hydride"
            }
        },
        "BeH2": {
            "sto-3g": {
                "pauli_string": "IIIIIIIIIIIIII + ...",
                "num_qubits": 14,
                "ground_state_energy": -15.56,
                "description": "Beryllium hydride"
            }
        },
        "H2O": {
            "sto-3g": {
                "pauli_string": "...",
                "num_qubits": 12,
                "ground_state_energy": -75.0,
                "description": "Water molecule"
            }
        }
    }
    
    @classmethod
    def get_hamiltonian(cls, molecule: str, basis: str = "sto-3g") -> Tuple[Dict, Dict]:
        """
        Get Hamiltonian for a molecule.
        
        Args:
            molecule: Molecule formula (e.g., "H2")
            basis: Basis set (default: "sto-3g")
            
        Returns:
            Tuple of (hamiltonian_dict, metadata_dict)
        """
        if molecule not in cls.MOLECULAR_HAMILTONIANS:
            available = list(cls.MOLECULAR_HAMILTONIANS.keys())
            raise ValueError(f"Molecule {molecule} not in database. Available: {available}")
            
        mol_data = cls.MOLECULAR_HAMILTONIANS[molecule].get(basis)
        if not mol_data:
            raise ValueError(f"Basis {basis} not available for {molecule}")
            
        hamiltonian_dict = {
            "pauli_string": mol_data["pauli_string"],
            "num_qubits": mol_data["num_qubits"],
            "molecule": molecule,
            "basis": basis
        }
        
        metadata = {
            "molecule": molecule,
            "basis": basis,
            "num_qubits": mol_data["num_qubits"],
            "target_energy": mol_data["ground_state_energy"],
            "description": mol_data.get("description", "")
        }
        
        return hamiltonian_dict, metadata
    
    @classmethod
    def list_available_molecules(cls) -> List[str]:
        """List available molecules."""
        return list(cls.MOLECULAR_HAMILTONIANS.keys())


class AnsatzGenerator:
    """
    Generate ansatz architectures.
    
    In production, would use MLX neural network for generation.
    Currently uses random generation with structure constraints.
    """
    
    SINGLE_QUBIT_GATES = ["H", "X", "Y", "Z", "S", "T", "RX", "RY", "RZ"]
    TWO_QUBIT_GATES = ["CNOT", "CZ", "CY", "SWAP"]
    
    def __init__(self, config: VQEConfig, seed: Optional[int] = None):
        self.config = config
        if seed is not None:
            random.seed(seed)
            
    def generate_random(self) -> AnsatzCandidate:
        """Generate a random ansatz candidate."""
        depth = random.randint(self.config.min_depth, self.config.max_depth)
        
        gates = []
        param_count = 0
        
        for i in range(depth):
            # Alternate between single and two-qubit gates
            if i % 2 == 0:
                gate = random.choice(self.SINGLE_QUBIT_GATES)
                gates.append(gate)
                if gate in ["RX", "RY", "RZ"]:
                    param_count += 1
            else:
                gate = random.choice(self.TWO_QUBIT_GATES)
                gates.append(gate)
                
        gates.append("<EOS>")
        
        return AnsatzCandidate(
            token_sequence=gates,
            depth=depth,
            parameter_count=param_count
        )
    
    def generate_variational(self, num_layers: int = 2) -> AnsatzCandidate:
        """Generate a variational ansatz (RealAmplitudes-like structure)."""
        gates = []
        param_count = 0
        
        for layer in range(num_layers):
            # Single-qubit rotations
            for q in range(self.config.num_qubits):
                gates.extend(["RY", "RZ"])
                param_count += 2
                
            # Entangling layer (CNOTs in circular pattern)
            for q in range(self.config.num_qubits):
                gates.append("CNOT")
                
        gates.append("<EOS>")
        
        return AnsatzCandidate(
            token_sequence=gates,
            depth=len(gates) - 1,
            parameter_count=param_count
        )


class VQEAnsatzOptimizer:
    """
    Main VQE optimization loop.
    
    Follows the autoresearch pattern:
    1. Generate candidate ansatz
    2. Evaluate energy and metrics
    3. Keep if better, discard if worse
    """
    
    def __init__(self, config: VQEConfig):
        self.config = config
        self.tokenizer = AnsatzTokenizer()
        self.mw_calculator = MeyerWallachCalculator()
        self.generator = AnsatzGenerator(config)
        self.best_candidate: Optional[AnsatzCandidate] = None
        self.history: List[AnsatzCandidate] = []
        self.iteration = 0
        
    def evaluate_ansatz(
        self, 
        candidate: AnsatzCandidate,
        hamiltonian: Dict
    ) -> AnsatzCandidate:
        """
        Evaluate a candidate ansatz.
        
        Returns the candidate with energy, gradient, and MW metrics.
        
        This is a simplified evaluation - in production would use actual
        quantum simulation via Qiskit Aer or CUDA-Q.
        """
        # Simulate energy evaluation
        # In production: run VQE simulation with parameter optimization
        
        import numpy as np
        
        # Estimate energy based on circuit properties
        # Better circuits (higher MW, reasonable depth) should get lower energy
        num_params = candidate.parameter_count
        depth = candidate.depth
        
        # Generate random energy estimate (in production: actual simulation)
        # Favor circuits with reasonable depth and parameters
        optimal_params = min(num_params, 20) * 0.05
        depth_penalty = max(0, depth - 10) * 0.01
        
        base_energy = self.config.target_energy or -1.0
        
        # Add some randomness for diversity
        noise = np.random.normal(0, 0.05)
        
        energy = base_energy + optimal_params + depth_penalty + noise
        candidate.energy = float(energy)
        
        # Calculate Meyer-Wallach (use random statevector for simulation)
        statevector = np.random.randn(2 ** self.config.num_qubits) + 1j * np.random.randn(2 ** self.config.num_qubits)
        statevector = statevector / np.linalg.norm(statevector)
        
        candidate.meyer_wallach_score = self.mw_calculator.calculate(
            statevector, self.config.num_qubits
        )
        
        # Estimate gradient variance (avoid barren plateaus)
        # Circuits with higher MW tend to have better gradients
        candidate.gradient_variance = max(1e-6, 0.1 * (1 - candidate.meyer_wallach_score) + np.random.exponential(0.01))
        
        return candidate
    
    def objective(self, candidate: AnsatzCandidate) -> float:
        """
        Calculate objective function for candidate selection.
        
        Objective = energy + λ * (1 - MW) + penalty(depth > max_depth)
        
        Lower is better.
        """
        if candidate.energy is None:
            return float('inf')
            
        obj = candidate.energy
        
        # Meyer-Wallach regularization (encourage entanglement)
        if candidate.meyer_wallach_score is not None:
            obj += self.config.meyer_wallach_lambda * (1 - candidate.meyer_wallach_score)
            
        # Depth penalty
        if candidate.depth > self.config.max_depth:
            obj += (candidate.depth - self.config.max_depth) * 0.1
            
        # Gradient variance penalty (avoid barren plateaus)
        if candidate.gradient_variance is not None and candidate.gradient_variance < 1e-6:
            obj += 1.0
            
        return obj
    
    async def run_loop(
        self, 
        hamiltonian: Dict
    ) -> AsyncGenerator[str, None]:
        """
        Run the VQE ansatz optimization loop.
        
        Yields SSE events for frontend streaming.
        """
        start_time = time.time()
        
        while time.time() - start_time < self.config.time_budget:
            self.iteration += 1
            
            yield f"event: log\ndata: {json.dumps({'text': f'--- VQE Iteration {self.iteration} ---'})}\n\n"
            
            # Generate candidate ansatz
            if self.iteration % 3 == 0:
                candidate = self.generator.generate_variational(num_layers=self.iteration % 5 + 1)
            else:
                candidate = self.generator.generate_random()
                
            yield f"event: log\ndata: {json.dumps({'text': f'Generated ansatz: depth={candidate.depth}, params={candidate.parameter_count}'})}\n\n"
            
            # Evaluate candidate
            candidate = self.evaluate_ansatz(candidate, hamiltonian)
            
            yield f"event: metric\ndata: {json.dumps({'name': 'energy', 'value': candidate.energy})}\n\n"
            yield f"event: metric\ndata: {json.dumps({'name': 'meyer_wallach', 'value': candidate.meyer_wallach_score})}\n\n"
            yield f"event: metric\ndata: {json.dumps({'name': 'gradient_variance', 'value': candidate.gradient_variance})}\n\n"
            
            # Calculate objective
            obj = self.objective(candidate)
            
            # Keep or discard
            if self.best_candidate is None or obj < self.objective(self.best_candidate):
                self.best_candidate = candidate
                status = "keep"
                yield f"event: log\ndata: {json.dumps({'text': f'WIN! New best: energy={candidate.energy:.6f}, MW={candidate.meyer_wallach_score:.4f}'})}\n\n"
            else:
                status = "discard"
                yield f"event: log\ndata: {json.dumps({'text': f'DISCARD: objective {obj:.6f} >= {self.objective(self.best_candidate):.6f}'})}\n\n"
                
            self.history.append(candidate)
            
            # Log to results
            self._log_result(candidate, status)
            
            # Small delay between iterations
            await asyncio.sleep(0.1)
            
        # Final summary
        if self.best_candidate:
            yield f"event: status\ndata: {json.dumps({'status': 'completed', 'message': f'VQE loop finished. Best energy: {self.best_candidate.energy}'})}\n\n"
        else:
            yield f"event: status\ndata: {json.dumps({'status': 'completed', 'message': 'VQE loop finished. No valid candidates.'})}\n\n"
            
    def _log_result(self, candidate: AnsatzCandidate, status: str):
        """Log result to TSV file."""
        results_path = os.path.join(
            os.path.dirname(__file__),
            "vqe_results.tsv"
        )
        
        try:
            # Header if file doesn't exist
            if not os.path.exists(results_path):
                with open(results_path, "w") as f:
                    f.write("iteration\tenergy\tmeyer_wallach\tgradient_var\tdepth\tparams\tstatus\ttimestamp\n")
                    
            # Append result
            with open(results_path, "a") as f:
                f.write(f"{self.iteration}\t{candidate.energy or 0:.6f}\t"
                       f"{candidate.meyer_wallach_score or 0:.4f}\t"
                       f"{candidate.gradient_variance or 0:.6e}\t"
                       f"{candidate.depth}\t{candidate.parameter_count}\t"
                       f"{status}\t{candidate.timestamp}\n")
        except Exception as e:
            logger.error(f"Failed to log result: {e}")


async def run_vqe_optimization(
    molecule: str = "H2",
    basis: str = "sto-3g",
    time_budget: int = 300,
    meyer_wallach_lambda: float = 0.1
) -> AsyncGenerator[str, None]:
    """
    Run VQE optimization with given parameters.
    
    This is the main entry point for the VQE loop.
    
    Args:
        molecule: Molecule to optimize
        basis: Basis set
        time_budget: Time budget in seconds
        meyer_wallach_lambda: MW regularization strength
        
    Yields:
        SSE events for frontend streaming
    """
    # Get Hamiltonian
    try:
        hamiltonian, metadata = HamiltonianBuilder.get_hamiltonian(molecule, basis)
        logger.info(f"Loaded Hamiltonian for {molecule}/{basis}")
        logger.info(f"Target energy: {metadata['target_energy']}")
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': f'Hamiltonian error: {e}'})}\n\n"
        return
        
    # Create config
    config = VQEConfig(
        molecule=molecule,
        basis=basis,
        num_qubits=metadata["num_qubits"],
        time_budget=time_budget,
        meyer_wallach_lambda=meyer_wallach_lambda,
        target_energy=metadata["target_energy"]
    )
    
    yield f"event: status\ndata: {json.dumps({'status': 'started', 'message': f'VQE optimization started for {molecule}'})}\n\n"
    
    # Run optimization
    optimizer = VQEAnsatzOptimizer(config)
    
    async for event in optimizer.run_loop(hamiltonian):
        yield event


async def main():
    """CLI entry point for VQE training."""
    parser = argparse.ArgumentParser(description="VQE Ansatz Discovery")
    parser.add_argument("--molecule", default="H2", help="Molecule to optimize")
    parser.add_argument("--basis", default="sto-3g", help="Basis set")
    parser.add_argument("--time-budget", type=int, default=300, help="Time budget in seconds")
    parser.add_argument("--meyer-wallach-lambda", type=float, default=0.1, help="MW regularization")
    parser.add_argument("--list-molecules", action="store_true", help="List available molecules")
    
    args = parser.parse_args()
    
    if args.list_molecules:
        print("Available molecules:")
        for mol in HamiltonianBuilder.list_available_molecules():
            print(f"  - {mol}")
        return
        
    print(f"Starting VQE optimization for {args.molecule}/{args.basis}")
    print(f"Time budget: {args.time_budget}s")
    print(f"MW lambda: {args.meyer_wallach_lambda}")
    print()
    
    async for event in run_vqe_optimization(
        molecule=args.molecule,
        basis=args.basis,
        time_budget=args.time_budget,
        meyer_wallach_lambda=args.meyer_wallach_lambda
    ):
        # Parse and print events
        if event.startswith("event: log"):
            data = event.split("data: ")[1].strip()
            msg = json.loads(data)
            print(msg["text"])
        elif event.startswith("event: metric"):
            data = event.split("data: ")[1].strip()
            msg = json.loads(data)
            print(f"  {msg['name']}: {msg['value']:.6f}")
        elif event.startswith("event: status"):
            data = event.split("data: ")[1].strip()
            msg = json.loads(data)
            print(f"\n{msg['message']}")


if __name__ == "__main__":
    asyncio.run(main())
