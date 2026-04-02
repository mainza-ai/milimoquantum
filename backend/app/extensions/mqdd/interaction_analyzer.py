"""Milimo Quantum — MQDD Interaction Analyzer.

Real protein-ligand interaction analysis using PLIP (Protein-Ligand Interaction Profiler).
"""
from __future__ import annotations

import logging
import tempfile
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Check PLIP availability
try:
    from plip.structure.preparation import PDBComplex
    from plip.exchange.report import BindingSiteReport
    PLIP_AVAILABLE = True
except ImportError:
    PLIP_AVAILABLE = False
    logger.info("PLIP not installed. Interaction analysis will fall back to LLM. Install with: pip install plip")


def analyze_protein_ligand_interactions(
    pdb_content: str,
    ligand_smiles: str
) -> Dict[str, Any]:
    """
    Analyze protein-ligand interactions using PLIP.
    
    Detects:
    - Hydrogen bonds
    - Hydrophobic contacts
    - Pi-stacking
    - Pi-cation interactions
    - Salt bridges
    - Water bridges
    - Halogen bonds
    - Metal complexes
    
    Args:
        pdb_content: PDB file content as string
        ligand_smiles: SMILES string of ligand (for reference)
    
    Returns:
        Dictionary with interaction list and summary statistics
    """
    if not PLIP_AVAILABLE:
        return {
            "status": "UNAVAILABLE",
            "message": "PLIP not installed. Install with: pip install plip",
            "interactions": [],
            "fallback": True
        }
    
    try:
        # Write PDB to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdb', delete=False) as f:
            f.write(pdb_content)
            pdb_path = f.name
        
        # Load structure
        pdbcomplex = PDBComplex()
        pdbcomplex.load_pdb(pdb_path)
        
        interactions = []
        interaction_counts = {
            "hydrogen_bonds": 0,
            "hydrophobic": 0,
            "pi_stacking": 0,
            "pi_cation": 0,
            "salt_bridges": 0,
            "water_bridges": 0,
            "halogen_bonds": 0,
            "metal_complexes": 0
        }
        
        # Analyze each ligand binding site
        for ligand in pdbcomplex.ligands:
            pdbcomplex.characterize_complex(ligand)
            
            # Get binding site report
            bs = BindingSiteReport(ligand)
            
            # Hydrogen bonds
            for hbond in bs.hbonds_pdb:
                interaction = {
                    "type": "hydrogen_bond",
                    "residue": hbond[0],
                    "residue_id": int(hbond[1]),
                    "chain": hbond[0][0] if hbond[0] else "",
                    "distance": float(hbond[4]),
                    "atom_donor": hbond[2],
                    "atom_acceptor": hbond[3],
                    "angle": float(hbond[5]) if len(hbond) > 5 else None
                }
                interactions.append(interaction)
                interaction_counts["hydrogen_bonds"] += 1
            
            # Hydrophobic contacts
            for hydro in bs.hydrophobic_contacts:
                interaction = {
                    "type": "hydrophobic",
                    "residue": hydro[0],
                    "residue_id": int(hydro[1]),
                    "chain": hydro[0][0] if hydro[0] else "",
                    "distance": float(hydro[3]),
                    "atom1": hydro[2] if len(hydro) > 2 else "",
                    "atom2": hydro[4] if len(hydro) > 4 else ""
                }
                interactions.append(interaction)
                interaction_counts["hydrophobic"] += 1
            
            # Pi-stacking
            for pistack in bs.pistacking:
                interaction = {
                    "type": "pi_stacking",
                    "residue": pistack[0],
                    "residue_id": int(pistack[1]),
                    "chain": pistack[0][0] if pistack[0] else "",
                    "distance": float(pistack[3]),
                    "angle": float(pistack[4]) if len(pistack) > 4 else None
                }
                interactions.append(interaction)
                interaction_counts["pi_stacking"] += 1
            
            # Pi-cation
            for picat in bs.pication:
                interaction = {
                    "type": "pi_cation",
                    "residue": picat[0],
                    "residue_id": int(picat[1]),
                    "chain": picat[0][0] if picat[0] else "",
                    "distance": float(picat[3])
                }
                interactions.append(interaction)
                interaction_counts["pi_cation"] += 1
            
            # Salt bridges
            for salt in bs.saltbridges:
                interaction = {
                    "type": "salt_bridge",
                    "residue": salt[0],
                    "residue_id": int(salt[1]),
                    "chain": salt[0][0] if salt[0] else "",
                    "distance": float(salt[3])
                }
                interactions.append(interaction)
                interaction_counts["salt_bridges"] += 1
            
            # Water bridges
            for water in bs.waterbridges:
                interaction = {
                    "type": "water_bridge",
                    "residue": water[0],
                    "residue_id": int(water[1]),
                    "chain": water[0][0] if water[0] else "",
                    "distance": float(water[3]),
                    "water_id": int(water[2]) if len(water) > 2 else None
                }
                interactions.append(interaction)
                interaction_counts["water_bridges"] += 1
            
            # Halogen bonds
            for halogen in bs.halogenbonds:
                interaction = {
                    "type": "halogen_bond",
                    "residue": halogen[0],
                    "residue_id": int(halogen[1]),
                    "chain": halogen[0][0] if halogen[0] else "",
                    "distance": float(halogen[3])
                }
                interactions.append(interaction)
                interaction_counts["halogen_bonds"] += 1
            
            # Metal complexes
            for metal in bs.metal_complexes:
                interaction = {
                    "type": "metal_complex",
                    "residue": metal[0],
                    "residue_id": int(metal[1]),
                    "chain": metal[0][0] if metal[0] else "",
                    "metal": metal[2] if len(metal) > 2 else "",
                    "distance": float(metal[3]) if len(metal) > 3 else None
                }
                interactions.append(interaction)
                interaction_counts["metal_complexes"] += 1
        
        # Cleanup temp file
        os.unlink(pdb_path)
        
        # Calculate binding score (simplified)
        binding_score = _calculate_binding_score(interactions, interaction_counts)
        
        return {
            "status": "SUCCESS",
            "interactions": interactions,
            "counts": interaction_counts,
            "total_interactions": len(interactions),
            "binding_score": binding_score,
            "ligand_smiles": ligand_smiles,
            "fallback": False
        }
        
    except Exception as e:
        logger.error(f"PLIP analysis failed: {e}")
        # Cleanup temp file if exists
        if 'pdb_path' in locals():
            try:
                os.unlink(pdb_path)
            except:
                pass
        
        return {
            "status": "ERROR",
            "message": str(e),
            "interactions": [],
            "fallback": True
        }


def _calculate_binding_score(
    interactions: List[Dict],
    counts: Dict[str, int]
) -> Dict[str, Any]:
    """
    Calculate a binding affinity score based on interactions.
    
    Uses simplified model:
    - Hydrogen bonds: strong contribution
    - Hydrophobic: moderate contribution
    - Pi-stacking: moderate contribution
    - Salt bridges: strong contribution
    """
    # Weight factors
    weights = {
        "hydrogen_bonds": 2.0,
        "hydrophobic": 1.0,
        "pi_stacking": 1.5,
        "pi_cation": 1.5,
        "salt_bridges": 3.0,
        "water_bridges": 0.5,
        "halogen_bonds": 1.5,
        "metal_complexes": 2.0
    }
    
    score = sum(counts.get(k, 0) * v for k, v in weights.items())
    
    # Normalize to 0-1 range (empirical)
    normalized_score = min(1.0, score / 20.0)
    
    # Affinity estimate (very simplified)
    # Lower is better for binding energy
    binding_energy_estimate = -5.0 - (score * 0.5)  # kJ/mol approximation
    
    return {
        "interaction_score": round(score, 2),
        "normalized_score": round(normalized_score, 3),
        "binding_energy_estimate_kj_mol": round(binding_energy_estimate, 2),
        "grade": _get_binding_grade(normalized_score)
    }


def _get_binding_grade(score: float) -> str:
    """Convert score to grade."""
    if score >= 0.8:
        return "Excellent"
    elif score >= 0.6:
        return "Good"
    elif score >= 0.4:
        return "Moderate"
    elif score >= 0.2:
        return "Weak"
    else:
        return "Very Weak"


def get_interaction_summary(interactions: List[Dict]) -> str:
    """
    Generate a human-readable summary of interactions.
    
    Args:
        interactions: List of interaction dictionaries
    
    Returns:
        Markdown-formatted summary string
    """
    if not interactions:
        return "No interactions detected."
    
    # Group by type
    by_type = {}
    for i in interactions:
        itype = i.get("type", "unknown")
        if itype not in by_type:
            by_type[itype] = []
        by_type[itype].append(i)
    
    summary = "### Interaction Summary\n\n"
    
    for itype, items in sorted(by_type.items()):
        summary += f"**{itype.replace('_', ' ').title()}** ({len(items)})\n"
        for item in items[:5]:  # Limit to 5 per type
            res = item.get("residue", "?")
            resid = item.get("residue_id", "?")
            dist = item.get("distance", "?")
            summary += f"  - {res}{resid}: {dist:.2f}Å\n"
        if len(items) > 5:
            summary += f"  - ... and {len(items) - 5} more\n"
        summary += "\n"
    
    return summary
