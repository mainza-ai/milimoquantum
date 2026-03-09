"""Milimo Quantum — D-Wave Quantum Provider.

Integration with the D-Wave Ocean SDK for Quantum Annealing.
"""
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

DWAVE_AVAILABLE = False
try:
    from dwave.system import DWaveSampler, EmbeddingComposite
    import dimod
    DWAVE_AVAILABLE = True
except ImportError:
    logger.warning("dwave-ocean-sdk not installed or available. D-Wave integration will be simulated.")


class DWaveProvider:
    """Wrapper for D-Wave Quantum Annealers and hybrid solvers."""
    
    def __init__(self):
        self.token = os.getenv("DWAVE_API_TOKEN")
        self.sampler = None
        self._initialize_sampler()

    def _initialize_sampler(self):
        if not DWAVE_AVAILABLE:
            return
            
        try:
            if self.token:
                self.sampler = EmbeddingComposite(DWaveSampler(token=self.token))
                logger.info("Connected to D-Wave cloud hardware.")
            else:
                self.sampler = dimod.SimulatedAnnealingSampler()
                logger.info("D-Wave SimulatedAnnealingSampler loaded (No API token found).")
        except Exception as e:
            logger.error(f"Failed to initialize D-Wave sampler: {e}")
            self.sampler = dimod.SimulatedAnnealingSampler() if DWAVE_AVAILABLE else None

    async def solve_qubo(self, qubo_dict: Dict[tuple, float], num_reads: int = 100) -> Dict[str, Any]:
        """Execute a QUBO on the D-Wave system or simulator."""
        if not self.sampler:
            return {"error": "D-Wave sampler unavailable."}
            
        try:
            sampleset = self.sampler.sample_qubo(qubo_dict, num_reads=num_reads)
            
            # Format results
            best_sample = sampleset.first.sample
            best_energy = sampleset.first.energy
            
            return {
                "best_sample": best_sample,
                "best_energy": best_energy,
                "info": sampleset.info,
                "provider": "D-Wave Hardware" if self.token and type(self.sampler) is EmbeddingComposite else "Simulated Annealing"
            }
        except Exception as e:
            logger.error(f"Error solving QUBO: {e}")
            return {"error": str(e)}

dwave_provider = DWaveProvider()
