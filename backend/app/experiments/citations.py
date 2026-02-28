"""Milimo Quantum — Academic Citation Export.

Generate BibTeX entries and Zotero-compatible exports for quantum
experiments, referencing the underlying algorithms, papers, and tools.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# ── Known algorithm citations ────────────────────────
ALGORITHM_CITATIONS = {
    "grover": {
        "key": "grover1996",
        "type": "article",
        "title": "A Fast Quantum Mechanical Algorithm for Database Search",
        "author": "Grover, Lov K.",
        "journal": "Proceedings of the 28th Annual ACM Symposium on Theory of Computing",
        "year": "1996",
        "pages": "212--219",
        "doi": "10.1145/237814.237866",
    },
    "shor": {
        "key": "shor1997",
        "type": "article",
        "title": "Polynomial-Time Algorithms for Prime Factorization and Discrete Logarithms on a Quantum Computer",
        "author": "Shor, Peter W.",
        "journal": "SIAM Journal on Computing",
        "year": "1997",
        "volume": "26",
        "number": "5",
        "pages": "1484--1509",
        "doi": "10.1137/S0097539795293172",
    },
    "vqe": {
        "key": "peruzzo2014",
        "type": "article",
        "title": "A variational eigenvalue solver on a photonic quantum processor",
        "author": "Peruzzo, Alberto and others",
        "journal": "Nature Communications",
        "year": "2014",
        "volume": "5",
        "doi": "10.1038/ncomms5213",
    },
    "qaoa": {
        "key": "farhi2014",
        "type": "article",
        "title": "A Quantum Approximate Optimization Algorithm",
        "author": "Farhi, Edward and Goldstone, Jeffrey and Gutmann, Sam",
        "journal": "arXiv preprint arXiv:1411.4028",
        "year": "2014",
        "eprint": "1411.4028",
    },
    "qpe": {
        "key": "kitaev1995",
        "type": "article",
        "title": "Quantum measurements and the Abelian Stabilizer Problem",
        "author": "Kitaev, A. Yu.",
        "journal": "arXiv preprint quant-ph/9511026",
        "year": "1995",
        "eprint": "quant-ph/9511026",
    },
    "qft": {
        "key": "coppersmith2002",
        "type": "article",
        "title": "An approximate Fourier transform useful in quantum computing",
        "author": "Coppersmith, Don",
        "journal": "arXiv preprint quant-ph/0201067",
        "year": "2002",
        "eprint": "quant-ph/0201067",
    },
    "qkd_bb84": {
        "key": "bennett1984",
        "type": "inproceedings",
        "title": "Quantum cryptography: Public key distribution and coin tossing",
        "author": "Bennett, Charles H. and Brassard, Gilles",
        "booktitle": "Proceedings of IEEE International Conference on Computers, Systems and Signal Processing",
        "year": "1984",
        "pages": "175--179",
    },
    "hhl": {
        "key": "harrow2009",
        "type": "article",
        "title": "Quantum Algorithm for Linear Systems of Equations",
        "author": "Harrow, Aram W. and Hassidim, Avinatan and Lloyd, Seth",
        "journal": "Physical Review Letters",
        "year": "2009",
        "volume": "103",
        "doi": "10.1103/PhysRevLett.103.150502",
    },
    "qiskit": {
        "key": "qiskit2024",
        "type": "misc",
        "title": "Qiskit: An Open-source Framework for Quantum Computing",
        "author": "{Qiskit contributors}",
        "year": "2024",
        "url": "https://github.com/Qiskit/qiskit",
        "doi": "10.5281/zenodo.2573505",
    },
    "surface_code": {
        "key": "fowler2012",
        "type": "article",
        "title": "Surface codes: Towards practical large-scale quantum computation",
        "author": "Fowler, Austin G. and Mariantoni, Matteo and Martinis, John M. and Cleland, Andrew N.",
        "journal": "Physical Review A",
        "year": "2012",
        "volume": "86",
        "doi": "10.1103/PhysRevA.86.032324",
    },
    "zne": {
        "key": "temme2017",
        "type": "article",
        "title": "Error Mitigation for Short-Depth Quantum Circuits",
        "author": "Temme, Kristan and Bravyi, Sergey and Gambetta, Jay M.",
        "journal": "Physical Review Letters",
        "year": "2017",
        "volume": "119",
        "doi": "10.1103/PhysRevLett.119.180509",
    },
    "bernstein_vazirani": {
        "key": "bernstein1993",
        "type": "inproceedings",
        "title": "Quantum complexity theory",
        "author": "Bernstein, Ethan and Vazirani, Umesh",
        "booktitle": "Proceedings of the 25th Annual ACM Symposium on Theory of Computing",
        "year": "1993",
        "pages": "11--20",
    },
    "deutsch_jozsa": {
        "key": "deutsch1992",
        "type": "article",
        "title": "Rapid solution of problems by quantum computation",
        "author": "Deutsch, David and Jozsa, Richard",
        "journal": "Proceedings of the Royal Society of London. Series A: Mathematical and Physical Sciences",
        "year": "1992",
        "volume": "439",
        "pages": "553--558",
    },
}
def format_bibtex(citation: dict) -> str:
    """Format a single citation as a BibTeX entry."""
    entry_type = citation.get("type", "misc")
    key = citation.get("key", "unknown")

    fields = []
    for field in ("title", "author", "journal", "booktitle", "year", "volume",
                  "number", "pages", "doi", "url", "eprint"):
        if field in citation:
            fields.append(f"  {field} = {{{citation[field]}}}")

    return f"@{entry_type}{{{key},\n" + ",\n".join(fields) + "\n}\n"


def generate_bibtex(
    algorithms: list[str] | None = None,
    include_qiskit: bool = True,
) -> str:
    """Generate BibTeX entries for specified algorithms.

    Args:
        algorithms: List of algorithm names (e.g., ["grover", "vqe", "qaoa"])
        include_qiskit: Whether to include the Qiskit citation

    Returns:
        BibTeX string with all entries
    """
    entries = []

    if include_qiskit and "qiskit" in ALGORITHM_CITATIONS:
        entries.append(format_bibtex(ALGORITHM_CITATIONS["qiskit"]))

    if algorithms:
        for algo in algorithms:
            algo_lower = algo.lower().replace(" ", "_").replace("-", "_")
            if algo_lower in ALGORITHM_CITATIONS:
                entries.append(format_bibtex(ALGORITHM_CITATIONS[algo_lower]))
    else:
        # Include all
        for name, citation in ALGORITHM_CITATIONS.items():
            if name != "qiskit" or not include_qiskit:
                entries.append(format_bibtex(citation))

    return "\n".join(entries)


def generate_zotero_json(
    algorithms: list[str] | None = None,
    include_qiskit: bool = True,
) -> list[dict]:
    """Generate Zotero-compatible JSON for specified algorithms.

    Returns a list of Zotero item dicts that can be imported directly.
    """
    items = []

    citations_to_export = {}
    if include_qiskit and "qiskit" in ALGORITHM_CITATIONS:
        citations_to_export["qiskit"] = ALGORITHM_CITATIONS["qiskit"]

    if algorithms:
        for algo in algorithms:
            algo_lower = algo.lower().replace(" ", "_").replace("-", "_")
            if algo_lower in ALGORITHM_CITATIONS:
                citations_to_export[algo_lower] = ALGORITHM_CITATIONS[algo_lower]
    else:
        citations_to_export = ALGORITHM_CITATIONS.copy()

    for name, citation in citations_to_export.items():
        item_type = "journalArticle" if citation.get("type") == "article" else "conferencePaper"
        item = {
            "itemType": item_type,
            "title": citation.get("title", ""),
            "creators": [
                {"creatorType": "author", "name": a.strip()}
                for a in citation.get("author", "").split(" and ")
            ],
            "date": citation.get("year", ""),
            "DOI": citation.get("doi", ""),
            "url": citation.get("url", ""),
            "publicationTitle": citation.get("journal", citation.get("booktitle", "")),
            "volume": citation.get("volume", ""),
            "pages": citation.get("pages", ""),
            "tags": [
                {"tag": "quantum computing"},
                {"tag": name},
                {"tag": "milimo-quantum"},
            ],
        }
        items.append(item)

    return items


def detect_algorithms_in_code(code: str) -> list[str]:
    """Detect which quantum algorithms are referenced in code.

    Scans for keyword patterns and returns matching algorithm names.
    """
    code_lower = code.lower()
    found = []

    patterns = {
        "grover": ["grover", "oracle", "diffusion_operator", "grover_operator"],
        "shor": ["shor", "continued_fraction", "order_finding", "period_finding"],
        "vqe": ["vqe", "variational_eigensolver", "ansatz"],
        "qaoa": ["qaoa", "approximate_optimization", "mixer"],
        "qpe": ["qpe", "phase_estimation", "eigenvalue"],
        "qft": ["qft", "fourier_transform", "inverse_qft"],
        "qkd_bb84": ["bb84", "qkd", "key_distribution"],
        "hhl": ["hhl", "linear_systems", "harrow"],
        "surface_code": ["surface_code", "stabilizer", "syndrome"],
        "zne": ["zne", "zero_noise", "error_mitigation", "noise_amplification"],
        "bernstein_vazirani": ["bernstein", "vazirani", "secret_integer"],
        "deutsch_jozsa": ["deutsch", "jozsa", "balanced", "constant"],
    }

    for algo, keywords in patterns.items():
        if any(kw in code_lower for kw in keywords):
            found.append(algo)

    return found


def generate_experiment_citation(
    title: str = "Quantum Experiment",
    author: str = "Milimo Quantum User",
    date: str | None = None,
    algorithms: list[str] | None = None,
    notes: str = "",
) -> dict:
    """Generate a complete citation package for an experiment.

    Returns BibTeX, Zotero JSON, and detected algorithm references.
    """
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    date_str: str = str(date)
    experiment_bib = {
        "key": f"milimo_{date_str.replace('-', '')}",
        "type": "misc",
        "title": title,
        "author": author,
        "year": date_str[0:4] if len(date_str) >= 4 else date_str,
        "note": notes or f"Generated by Milimo Quantum on {date}",
        "url": "https://milimoquantum.com",
    }

    algo_bibtex = generate_bibtex(algorithms, include_qiskit=True)
    experiment_bibtex = format_bibtex(experiment_bib)
    full_bibtex = experiment_bibtex + "\n" + algo_bibtex

    return {
        "experiment_bibtex": experiment_bibtex,
        "algorithm_bibtex": algo_bibtex,
        "full_bibtex": full_bibtex,
        "zotero_json": generate_zotero_json(algorithms),
        "detected_algorithms": algorithms or [],
    }
