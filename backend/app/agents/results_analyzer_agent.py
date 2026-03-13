"""Milimo Quantum — Autoresearch Results Analyzer Agent.

Reads results.tsv and provides summaries of the experimental progress.
"""
from __future__ import annotations
import os
import logging
from app.extensions.autoresearch.workflow import AUTORESEARCH_DIR, get_results

logger = logging.getLogger(__name__)

def get_performance_summary() -> str:
    """Read results.tsv and generate a markdown summary."""
    results = get_results()
    if "error" in results:
        return f"Error reading results: {results['error']}"
    
    if not results.get("rows"):
        return "No experiment results found yet. Start a research loop to see data."
    
    cols = results["columns"]
    rows = results["rows"]
    
    # Generate a markdown table
    header = "| " + " | ".join(cols) + " |"
    separator = "| " + " | ".join(["---"] * len(cols)) + " |"
    table_rows = []
    for r in rows:
        table_rows.append("| " + " | ".join(r) + " |")
    
    table = "\n".join([header, separator] + table_rows)
    
    # Trend Analysis
    try:
        val_bpb_idx = cols.index("val_bpb")
        initial_bpb = float(rows[0][val_bpb_idx])
        latest_bpb = float(rows[-1][val_bpb_idx])
        
        diff = initial_bpb - latest_bpb
        improvement = (diff / initial_bpb) * 100 if initial_bpb > 0 else 0
        
        summary = f"### Training Trend Analysis\n"
        summary += f"- **Initial val_bpb**: {initial_bpb:.6f}\n"
        summary += f"- **Latest val_bpb**: {latest_bpb:.6f}\n"
        
        if diff > 0:
            summary += f"- **Status**: Improvement of **{improvement:.2f}%** detected! 🎉\n"
        else:
            summary += f"- **Status**: No significant improvement over baseline yet.\n"
            
    except Exception as e:
        summary = f"\n*Trend analysis unavailable: {e}*"

    return f"## Autoresearch Results Summary\n\n{table}\n\n{summary}"

def try_quick_topic(message: str) -> str | None:
    """Try to match high-level result analysis keywords."""
    lower = message.lower()
    keywords = ["analyze results", "explain results", "performance summary", "training progress", "bpb trend"]
    
    if any(kw in lower for kw in keywords):
        return get_performance_summary()
    
    return None
