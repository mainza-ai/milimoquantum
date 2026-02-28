"""Milimo Quantum — PubChem Molecular Data Feed.

Fetches molecular data from PubChem for the Chemistry Agent's VQE simulations.
Uses the free PubChem PUG REST API (no API key required).
"""
from __future__ import annotations

import json
import logging
import urllib.request
import ssl
import certifi
from typing import Any

logger = logging.getLogger(__name__)

PUBCHEM_API = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def search_compound(name: str) -> dict[str, Any] | None:
    """Search PubChem for a compound by name.

    Returns dict with: cid, name, formula, weight, smiles, inchi, atoms.
    """
    try:
        url = f"{PUBCHEM_API}/compound/name/{urllib.request.quote(name)}/JSON"
        context = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(url, headers={"User-Agent": "MilimoQuantum/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            data = json.loads(response.read())

        compound = data.get("PC_Compounds", [{}])[0]
        props = {}
        for prop in compound.get("props", []):
            label = prop.get("urn", {}).get("label", "")
            value = prop.get("value", {})
            if label == "IUPAC Name" and prop.get("urn", {}).get("name") == "Preferred":
                props["iupac_name"] = value.get("sval", "")
            elif label == "Molecular Formula":
                props["formula"] = value.get("sval", "")
            elif label == "Molecular Weight":
                props["weight"] = value.get("fval") or value.get("sval")
            elif label == "SMILES" and prop.get("urn", {}).get("name") == "Canonical":
                props["smiles"] = value.get("sval", "")
            elif label == "InChI":
                props["inchi"] = value.get("sval", "")

        # Count atoms
        atoms = compound.get("atoms", {})
        atom_count = len(atoms.get("element", []))

        return {
            "cid": compound.get("id", {}).get("id", {}).get("cid"),
            "name": name,
            "formula": props.get("formula", ""),
            "weight": props.get("weight"),
            "smiles": props.get("smiles", ""),
            "inchi": props.get("inchi", ""),
            "iupac_name": props.get("iupac_name", ""),
            "atom_count": atom_count,
        }

    except Exception as e:
        logger.error(f"PubChem API error for '{name}': {e}")
        return None


def get_molecule_qubits(compound: dict) -> int:
    """Estimate the number of qubits needed for VQE simulation.

    Rough heuristic: 2 qubits per heavy atom (non-hydrogen).
    """
    atom_count = compound.get("atom_count", 2)
    # Approximate: heavy atoms ≈ 60% of total atoms for organic molecules
    heavy_atoms = max(2, int(atom_count * 0.6))
    return heavy_atoms * 2


def format_molecule_markdown(compound: dict) -> str:
    """Format compound data as markdown for the Chemistry Agent."""
    if not compound:
        return "Compound not found in PubChem."

    qubits = get_molecule_qubits(compound)
    lines = [
        f"## {compound['name']} — Molecular Data",
        f"",
        f"| Property | Value |",
        f"|----------|-------|",
        f"| **Formula** | {compound.get('formula', '—')} |",
        f"| **Weight** | {compound.get('weight', '—')} g/mol |",
        f"| **SMILES** | `{compound.get('smiles', '—')}` |",
        f"| **Atoms** | {compound.get('atom_count', '—')} |",
        f"| **PubChem CID** | [{compound.get('cid', '—')}](https://pubchem.ncbi.nlm.nih.gov/compound/{compound.get('cid', '')}) |",
        f"",
        f"### VQE Estimation",
        f"- **Estimated qubits:** ~{qubits} (2 per heavy atom)",
        f"- **Feasibility:** {'✅ Laptop simulation' if qubits <= 20 else '⚠️ Needs cloud QPU' if qubits <= 50 else '❌ Beyond current hardware'}",
    ]
    return "\n".join(lines)
