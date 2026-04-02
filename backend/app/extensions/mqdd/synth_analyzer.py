"""Milimo Quantum — MQDD Synthesizability Analyzer.

Real synthesis accessibility scoring using multiple methods:
- RDKit SAscore
- SCScore (Synthesis Complexity Score)
- Complexity metrics
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Check RDKit availability
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors, Lipinski, Crippen
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    logger.info("RDKit not installed. Synthesizability scoring unavailable. Install with: pip install rdkit")

# Check SCScore availability
try:
    from scscore.standalone_model_numpy import SCScorer
    SCSCORE_AVAILABLE = True
except ImportError:
    SCSCORE_AVAILABLE = False
    logger.info("SCScore not installed. Install with: pip install scscore")


def calculate_synthesis_score(smiles: str) -> Dict[str, Any]:
    """
    Calculate Synthetic Accessibility (SA) score using multiple methods.
    
    Methods:
    1. RDKit SAscore (1-10, lower is better)
    2. SCScore (1-5, lower is better)  
    3. Complexity metrics (rings, rotatable bonds, stereocenters)
    4. QED (Quant Estimate of Drug-likeness)
    
    Args:
        smiles: SMILES string of molecule
    
    Returns:
        Dictionary with scores and difficulty assessment
    """
    if not RDKIT_AVAILABLE:
        return {
            "status": "UNAVAILABLE",
            "message": "RDKit not installed. Install with: pip install rdkit",
            "smiles": smiles,
            "fallback": True
        }
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {
                "status": "ERROR",
                "message": "Invalid SMILES string",
                "smiles": smiles,
                "fallback": True
            }
        
        results = {
            "smiles": smiles,
            "status": "SUCCESS",
            "fallback": False
        }
        
        # 1. RDKit SAscore
        results["sa_score"] = _calculate_sa_score(mol)
        
        # 2. SCScore
        results["sc_score"] = _calculate_sc_score(smiles)
        
        # 3. Complexity metrics
        complexity = _calculate_complexity(mol)
        results.update(complexity)
        
        # 4. QED (drug-likeness)
        results["qed"] = _calculate_qed(mol)
        
        # 5. Lipinski Rule of 5
        results["lipinski"] = _check_lipinski(mol)
        
        # 6. Overall assessment
        results["synthesis_difficulty"] = _assess_difficulty(results)
        results["drug_likeness"] = _assess_drug_likeness(results)
        
        # 7. Combined score (0-100, higher is better/synthesizable)
        results["combined_score"] = _calculate_combined_score(results)
        
        return results
        
    except Exception as e:
        logger.error(f"Synthesis scoring failed: {e}")
        return {
            "status": "ERROR",
            "message": str(e),
            "smiles": smiles,
            "fallback": True
        }


def _calculate_sa_score(mol) -> Optional[float]:
    """Calculate RDKit Synthetic Accessibility score (1-10)."""
    try:
        from rdkit.Chem import RDConfig
        import sys
        import os
        
        # Try to import sascorer
        sa_path = os.path.join(RDConfig.RDContribDir, 'SA_Scores')
        if os.path.exists(sa_path):
            sys.path.append(sa_path)
            try:
                import sascorer
                return round(sascorer.calculateScore(mol), 2)
            except ImportError:
                pass
        
        # Fallback: approximate SA score from complexity
        # Simplified model: more complex = higher SA
        num_rings = rdMolDescriptors.CalcNumRings(mol)
        num_rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
        num_stereo = rdMolDescriptors.CalcNumAtomStereoCenters(mol)
        
        # Approximate SA score
        approx_sa = 1.0 + num_rings * 0.5 + num_rotatable * 0.1 + num_stereo * 0.3
        return round(min(10.0, approx_sa), 2)
        
    except Exception as e:
        logger.warning(f"SA score calculation failed: {e}")
        return None


def _calculate_sc_score(smiles: str) -> Optional[float]:
    """Calculate SCScore (1-5)."""
    if not SCSCORE_AVAILABLE:
        return None
    
    try:
        scorer = SCScorer()
        scorer.restore()
        score = scorer.get_score_from_smiles(smiles)
        return round(float(score), 2)
    except Exception as e:
        logger.warning(f"SCScore calculation failed: {e}")
        return None


def _calculate_complexity(mol) -> Dict[str, Any]:
    """Calculate molecular complexity metrics."""
    try:
        return {
            "num_rings": rdMolDescriptors.CalcNumRings(mol),
            "num_rotatable_bonds": rdMolDescriptors.CalcNumRotatableBonds(mol),
            "num_stereocenters": rdMolDescriptors.CalcNumAtomStereoCenters(mol),
            "num_heavy_atoms": rdMolDescriptors.CalcNumHeavyAtoms(mol),
            "num_hba": rdMolDescriptors.CalcNumHBA(mol),
            "num_hbd": rdMolDescriptors.CalcNumHBD(mol),
            "mw": round(Descriptors.MolWt(mol), 2),
            "logp": round(Crippen.MolLogP(mol), 2),
            "tpsa": round(rdMolDescriptors.CalcTPSA(mol), 2),
        }
    except Exception as e:
        logger.warning(f"Complexity calculation failed: {e}")
        return {}


def _calculate_qed(mol) -> Optional[float]:
    """Calculate QED (Quant Estimate of Drug-likeness)."""
    try:
        from rdkit.Chem.QED import qed
        return round(qed(mol), 3)
    except Exception as e:
        logger.warning(f"QED calculation failed: {e}")
        return None


def _check_lipinski(mol) -> Dict[str, bool]:
    """Check Lipinski Rule of 5."""
    try:
        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        hbd = Lipinski.NumHDonors(mol)
        hba = Lipinski.NumHAcceptors(mol)
        
        return {
            "mw_lt_500": mw < 500,
            "logp_lt_5": logp < 5,
            "hbd_le_5": hbd <= 5,
            "hba_le_10": hba <= 10,
            "passes_all": (mw < 500 and logp < 5 and hbd <= 5 and hba <= 10),
            "violations": sum([
                mw >= 500,
                logp >= 5,
                hbd > 5,
                hba > 10
            ])
        }
    except Exception as e:
        logger.warning(f"Lipinski check failed: {e}")
        return {}


def _assess_difficulty(results: Dict) -> str:
    """Assess overall synthesis difficulty."""
    sa = results.get("sa_score")
    sc = results.get("sc_score")
    
    # Use available scores
    if sa is not None:
        if sa < 3:
            return "Easy"
        elif sa < 6:
            return "Moderate"
        else:
            return "Difficult"
    
    if sc is not None:
        if sc < 2:
            return "Easy"
        elif sc < 3.5:
            return "Moderate"
        else:
            return "Difficult"
    
    # Fallback to complexity
    complexity = results.get("complexity_score", 0)
    if complexity < 3:
        return "Easy"
    elif complexity < 6:
        return "Moderate"
    else:
        return "Difficult"


def _assess_drug_likeness(results: Dict) -> str:
    """Assess drug-likeness."""
    qed = results.get("qed")
    lipinski = results.get("lipinski", {})
    
    if qed is not None:
        if qed >= 0.7:
            return "Excellent"
        elif qed >= 0.5:
            return "Good"
        elif qed >= 0.3:
            return "Moderate"
        else:
            return "Poor"
    
    if lipinski.get("passes_all", False):
        return "Good"
    elif lipinski.get("violations", 2) <= 1:
        return "Moderate"
    else:
        return "Poor"


def _calculate_combined_score(results: Dict) -> int:
    """
    Calculate combined synthesizability score (0-100).
    
    Higher is better (easier to synthesize, more drug-like).
    """
    score = 100
    
    # SA score penalty (higher SA = harder)
    sa = results.get("sa_score")
    if sa is not None:
        score -= (sa - 1) * 5  # SA ranges 1-10
    
    # SC score penalty
    sc = results.get("sc_score")
    if sc is not None:
        score -= (sc - 1) * 10  # SC ranges 1-5
    
    # Complexity penalties
    rings = results.get("num_rings", 0)
    if rings > 3:
        score -= (rings - 3) * 5
    
    stereo = results.get("num_stereocenters", 0)
    if stereo > 2:
        score -= (stereo - 2) * 8
    
    # Lipinski bonus/penalty
    lipinski = results.get("lipinski", {})
    violations = lipinski.get("violations", 0)
    score -= violations * 10
    
    # QED bonus
    qed = results.get("qed")
    if qed is not None:
        score = score * 0.7 + qed * 30  # Blend with QED
    
    return max(0, min(100, int(score)))


def get_synthesis_summary(results: Dict) -> str:
    """
    Generate human-readable synthesis summary.
    
    Args:
        results: Results from calculate_synthesis_score
    
    Returns:
        Markdown-formatted summary string
    """
    if results.get("status") != "SUCCESS":
        return f"**Error:** {results.get('message', 'Unknown error')}"
    
    summary = f"""### Synthesis Analysis for `{results.get('smiles', 'Unknown')}`

**Overall Assessment:** {results.get('synthesis_difficulty', 'Unknown')}
**Drug-likeness:** {results.get('drug_likeness', 'Unknown')}
**Combined Score:** {results.get('combined_score', 'N/A')}/100

#### Scores
| Metric | Value | Interpretation |
|--------|-------|----------------|
| SA Score | {results.get('sa_score', 'N/A')} | {'(lower is better)' if results.get('sa_score') else ''} |
| SCScore | {results.get('sc_score', 'N/A')} | {'(lower is better)' if results.get('sc_score') else ''} |
| QED | {results.get('qed', 'N/A')} | {'(higher is better)' if results.get('qed') else ''} |

#### Molecular Properties
- **Molecular Weight:** {results.get('mw', 'N/A')} Da
- **LogP:** {results.get('logp', 'N/A')}
- **TPSA:** {results.get('tpsa', 'N/A')} Å²
- **Rings:** {results.get('num_rings', 'N/A')}
- **Rotatable Bonds:** {results.get('num_rotatable_bonds', 'N/A')}
- **Stereocenters:** {results.get('num_stereocenters', 'N/A')}

#### Lipinski Rule of 5
- MW < 500: {'✓' if results.get('lipinski', {}).get('mw_lt_500') else '✗'}
- LogP < 5: {'✓' if results.get('lipinski', {}).get('logp_lt_5') else '✗'}
- HBD ≤ 5: {'✓' if results.get('lipinski', {}).get('hbd_le_5') else '✗'}
- HBA ≤ 10: {'✓' if results.get('lipinski', {}).get('hba_le_10') else '✗'}
- **Violations:** {results.get('lipinski', {}).get('violations', 'N/A')}
"""
    
    return summary
