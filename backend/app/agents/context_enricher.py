"""Milimo Quantum — Context Enricher.

Dynamically injects live data (Yahoo Finance, arXiv, PubChem) and agent memory
into agent system prompts before the LLM call.

This is the bridge between the static agent prompts and the live feed connectors.
"""
from __future__ import annotations

import logging
import re
from app.models.schemas import AgentType

logger = logging.getLogger(__name__)

# Common stock ticker pattern
_TICKER_RE = re.compile(r'\b([A-Z]{1,5})\b')

# Known ticker symbols (subset for fast validation)
_KNOWN_TICKERS = {
    "AAPL", "GOOGL", "GOOG", "MSFT", "AMZN", "META", "TSLA", "NVDA",
    "JPM", "BAC", "GS", "V", "MA", "UNH", "JNJ", "PFE", "LLY",
    "BRK", "WMT", "HD", "PG", "KO", "PEP", "COST", "MCD",
    "NFLX", "DIS", "CMCSA", "INTC", "AMD", "QCOM", "AVGO",
    "IBM", "CRM", "ORCL", "CSCO", "ADBE", "NOW", "SNOW",
    "XOM", "CVX", "COP", "BA", "CAT", "GE", "MMM", "HON",
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO",
}

# Common molecule names
_MOLECULES = {
    "water": "water", "h2o": "water",
    "hydrogen": "hydrogen", "h2": "hydrogen",
    "lithium hydride": "lithium hydride", "lih": "lithium hydride",
    "aspirin": "aspirin", "acetylsalicylic acid": "aspirin",
    "caffeine": "caffeine",
    "ethanol": "ethanol", "alcohol": "ethanol",
    "methane": "methane", "ch4": "methane",
    "ammonia": "ammonia", "nh3": "ammonia",
    "benzene": "benzene",
    "glucose": "glucose",
    "penicillin": "penicillin",
    "ibuprofen": "ibuprofen",
    "paracetamol": "paracetamol", "acetaminophen": "paracetamol",
}


async def enrich_prompt(
    agent_type: AgentType,
    message: str,
    base_prompt: str,
) -> str:
    """Enrich an agent's system prompt with live context data.

    Fetches relevant data from feeds and memory, appends it to the
    base system prompt. Non-blocking — failures return the base prompt.
    """
    sections: list[str] = [base_prompt]

    try:
        # Agent-specific enrichment
        if agent_type == AgentType.FINANCE:
            data = _enrich_finance(message)
            if data:
                sections.append(data)

        elif agent_type == AgentType.RESEARCH:
            data = _enrich_research(message)
            if data:
                sections.append(data)

        elif agent_type == AgentType.CHEMISTRY:
            data = _enrich_chemistry(message)
            if data:
                sections.append(data)

        # Memory enrichment for all agents
        memory_ctx = await _enrich_from_memory(agent_type, message)
        if memory_ctx:
            sections.append(memory_ctx)

    except Exception as e:
        logger.warning(f"Context enrichment error (non-fatal): {e}")

    return "\n\n".join(sections)


def build_data_preamble(agent_type: AgentType, message: str) -> str | None:
    """Build a user-facing markdown data section that is streamed DIRECTLY
    to the user as chat tokens BEFORE the LLM generates its response.

    This guarantees the user always sees real data (prices, papers,
    molecules) regardless of how well the LLM interprets the data.
    Returns None if no relevant data found.
    """
    try:
        if agent_type == AgentType.FINANCE:
            return _build_finance_preamble(message)
        elif agent_type == AgentType.RESEARCH:
            return _build_research_preamble(message)
        elif agent_type == AgentType.CHEMISTRY:
            return _build_chemistry_preamble(message)
    except Exception as e:
        logger.warning(f"Data preamble build failed (non-fatal): {e}")
    return None


def _build_finance_preamble(message: str) -> str | None:
    """Build a rich market data section for the user."""
    tickers = _extract_tickers(message)
    if not tickers:
        return None

    try:
        from app.feeds import get_stock_prices, get_portfolio_summary

        prices = get_stock_prices(tickers)
        if not prices:
            return None

        lines = ["## 📊 Live Market Data\n"]

        # Price table
        lines.append("| Symbol | Company | Price | Change | Sector |")
        lines.append("|--------|---------|-------|--------|--------|")

        for sym, data in prices.items():
            if "error" in data:
                lines.append(f"| {sym} | — | — | — | — |")
                continue

            price = data.get("price", 0)
            change = data.get("change", 0)
            pct = data.get("change_pct", 0)
            name = data.get("name", sym)
            sector = data.get("sector", "")
            mock = " ⚠️" if data.get("mock") else ""

            arrow = "📈" if change >= 0 else "📉"
            lines.append(
                f"| **{sym}** | {name} | ${price:.2f}{mock} | {arrow} {change:+.2f} ({pct:+.1f}%) | {sector} |"
            )

        lines.append("")

        # Correlation matrix
        if len(tickers) >= 2:
            try:
                from app.feeds import get_correlation_matrix
                corr = get_correlation_matrix(tickers, period="6mo")
                if corr and "matrix" in corr:
                    mat = corr["matrix"]
                    syms = corr["symbols"]
                    # Only show if we have real data (not all NaN)
                    has_data = any(
                        not (isinstance(mat[i][j], float) and str(mat[i][j]) == "nan")
                        for i in range(len(syms)) for j in range(len(syms)) if i != j
                    )
                    if has_data:
                        lines.append("### Correlation Matrix (6-month)\n")
                        lines.append("| | " + " | ".join(syms) + " |")
                        lines.append("|" + "|".join(["---" for _ in range(len(syms) + 1)]) + "|")
                        for i, sym in enumerate(syms):
                            row = []
                            for j in range(len(syms)):
                                val = mat[i][j]
                                row.append(f"{val:.2f}" if isinstance(val, (int, float)) and str(val) != "nan" else "—")
                            lines.append(f"| **{sym}** | " + " | ".join(row) + " |")
                        lines.append("")
            except Exception:
                pass

        # Portfolio summary
        try:
            summary = get_portfolio_summary(tickers)
            if summary:
                lines.append("### Portfolio Summary\n")
                lines.append(summary)
                lines.append("")
        except Exception:
            pass

        lines.append("---\n")
        lines.append("### Quantum Analysis\n")

        logger.info(f"Finance preamble built for {len(tickers)} tickers")
        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"Finance preamble failed: {e}")
        return None


def _build_research_preamble(message: str) -> str | None:
    """Build a recent papers section for the user."""
    lower = message.lower()
    skip_words = {"explain", "what", "is", "are", "the", "how", "does", "about", "tell", "me", "research"}
    topic_words = [w for w in lower.split() if w not in skip_words and len(w) > 2]
    query = " ".join(topic_words[:5])

    if not query or len(query) < 5:
        return None

    try:
        from app.feeds.arxiv import search_papers

        papers = search_papers(query, max_results=3, category="quant-ph")
        if not papers:
            return None

        lines = ["## 📄 Recent Research\n"]

        for i, p in enumerate(papers, 1):
            authors = ", ".join(p["authors"][:3])
            if len(p["authors"]) > 3:
                authors += " et al."
            lines.append(f"**{i}. [{p['title']}]({p['url']})**")
            lines.append(f"*{authors}* — {p['published']}")
            lines.append(f"> {p['abstract'][:250]}...\n")

        lines.append("---\n")
        lines.append("### Explanation\n")

        logger.info(f"Research preamble built with {len(papers)} papers")
        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"Research preamble failed: {e}")
        return None


def _build_chemistry_preamble(message: str) -> str | None:
    """Build a molecular data section for the user."""
    lower = message.lower()
    molecule_name = None
    for key, canonical in _MOLECULES.items():
        if key in lower:
            molecule_name = canonical
            break

    if not molecule_name:
        return None

    try:
        from app.feeds.pubchem import search_compound, get_molecule_qubits

        compound = search_compound(molecule_name)
        if not compound:
            return None

        qubits = get_molecule_qubits(compound)

        lines = [
            f"## 🧪 Molecule: {molecule_name.title()}\n",
            f"| Property | Value |",
            f"|----------|-------|",
            f"| **Formula** | {compound.get('formula', '—')} |",
            f"| **Molecular Weight** | {compound.get('weight', '—')} g/mol |",
            f"| **SMILES** | `{compound.get('smiles', '—')}` |",
            f"| **IUPAC Name** | {compound.get('iupac_name', '—')} |",
            f"| **Atom Count** | {compound.get('atom_count', '—')} |",
            f"| **PubChem CID** | [{compound.get('cid', '—')}](https://pubchem.ncbi.nlm.nih.gov/compound/{compound.get('cid', '')}) |",
            f"| **Est. VQE Qubits** | ~{qubits} |",
            f"",
            f"---\n",
            f"### VQE Simulation\n",
        ]

        logger.info(f"Chemistry preamble built for {molecule_name}")
        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"Chemistry preamble failed: {e}")
        return None


def _extract_tickers(message: str) -> list[str]:
    """Extract stock ticker symbols from a message."""
    # Find all uppercase words that look like tickers
    candidates = _TICKER_RE.findall(message)
    # Filter to known tickers
    tickers = [t for t in candidates if t in _KNOWN_TICKERS]

    # Also check for common company names
    lower = message.lower()
    name_map = {
        "apple": "AAPL", "google": "GOOGL", "microsoft": "MSFT",
        "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA",
        "facebook": "META", "netflix": "NFLX", "disney": "DIS",
        "ibm": "IBM", "intel": "INTC", "amd": "AMD",
        "jpmorgan": "JPM", "goldman": "GS",
        "pfizer": "PFE", "johnson": "JNJ",
    }
    for name, ticker in name_map.items():
        if name in lower and ticker not in tickers:
            tickers.append(ticker)

    return tickers[:10]  # Cap at 10 symbols


def _enrich_finance(message: str) -> str | None:
    """Fetch real market data for mentioned stocks."""
    tickers = _extract_tickers(message)
    if not tickers:
        return None

    try:
        from app.feeds import get_stock_prices, get_portfolio_summary

        prices = get_stock_prices(tickers)
        if not prices:
            return None

        lines = [
            "\n--- LIVE MARKET DATA (use this in your response) ---",
            "The following is REAL market data — include these actual prices and numbers in your response.",
            "Do NOT make up prices. Use the exact values below.\n",
        ]

        for sym, data in prices.items():
            if "error" in data:
                lines.append(f"- {sym}: data unavailable")
                continue

            price = data.get("price", 0)
            change = data.get("change", 0)
            pct = data.get("change_pct", 0)
            name = data.get("name", sym)
            sector = data.get("sector", "Unknown")
            mock = " (simulated)" if data.get("mock") else ""

            arrow = "📈" if change >= 0 else "📉"
            lines.append(
                f"- **{sym}** ({name}): ${price:.2f} {arrow} {change:+.2f} ({pct:+.1f}%) | Sector: {sector}{mock}"
            )

        if len(tickers) >= 2:
            try:
                from app.feeds import get_correlation_matrix
                corr = get_correlation_matrix(tickers, period="6mo")
                if corr and "matrix" in corr:
                    lines.append("\n**Correlation Matrix (6-month):**")
                    syms = corr["symbols"]
                    lines.append("| | " + " | ".join(syms) + " |")
                    lines.append("|-" + "|-".join(["-" for _ in syms]) + "|")
                    for i, sym in enumerate(syms):
                        row = [f"{corr['matrix'][i][j]:.2f}" for j in range(len(syms))]
                        lines.append(f"| {sym} | " + " | ".join(row) + " |")
            except Exception:
                pass

        lines.append("\n--- END LIVE DATA ---\n")
        logger.info(f"Finance context enriched with {len(tickers)} tickers")
        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"Finance enrichment failed: {e}")
        return None


def _enrich_research(message: str) -> str | None:
    """Fetch relevant arXiv papers for the query."""
    # Extract the research topic (strip common filler words)
    lower = message.lower()
    skip_words = {"explain", "what", "is", "are", "the", "how", "does", "about", "tell", "me"}
    topic_words = [w for w in lower.split() if w not in skip_words and len(w) > 2]
    query = " ".join(topic_words[:5])

    if not query or len(query) < 5:
        return None

    try:
        from app.feeds.arxiv import search_papers

        papers = search_papers(query, max_results=3, category="quant-ph")
        if not papers:
            return None

        lines = [
            "\n--- RECENT RESEARCH (reference these in your response) ---",
            "The following are real recent papers from arXiv. Mention relevant ones.\n",
        ]

        for i, p in enumerate(papers, 1):
            authors = ", ".join(p["authors"][:2])
            if len(p["authors"]) > 2:
                authors += " et al."
            lines.append(f"{i}. **{p['title']}** ({p['published']})")
            lines.append(f"   Authors: {authors}")
            lines.append(f"   {p['abstract'][:200]}...")
            lines.append(f"   Link: {p['url']}\n")

        lines.append("--- END RECENT RESEARCH ---\n")
        logger.info(f"Research context enriched with {len(papers)} papers")
        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"Research enrichment failed: {e}")
        return None


def _enrich_chemistry(message: str) -> str | None:
    """Fetch molecular data from PubChem for mentioned molecules."""
    lower = message.lower()

    # Find molecule name in the message
    molecule_name = None
    for key, canonical in _MOLECULES.items():
        if key in lower:
            molecule_name = canonical
            break

    if not molecule_name:
        return None

    try:
        from app.feeds.pubchem import search_compound, get_molecule_qubits

        compound = search_compound(molecule_name)
        if not compound:
            return None

        qubits = get_molecule_qubits(compound)

        lines = [
            "\n--- MOLECULE DATA (use this in your response) ---",
            f"Real molecular data from PubChem for **{molecule_name}**:\n",
            f"- **Formula:** {compound.get('formula', '—')}",
            f"- **Molecular Weight:** {compound.get('weight', '—')} g/mol",
            f"- **SMILES:** {compound.get('smiles', '—')}",
            f"- **IUPAC Name:** {compound.get('iupac_name', '—')}",
            f"- **Atom Count:** {compound.get('atom_count', '—')}",
            f"- **PubChem CID:** {compound.get('cid', '—')}",
            f"- **Estimated VQE Qubits:** ~{qubits}",
            f"",
            f"Use these values for accurate VQE simulation parameters.",
            f"Adjust qubit count in your circuit to match this molecule.",
            "\n--- END MOLECULE DATA ---\n",
        ]

        logger.info(f"Chemistry context enriched with {molecule_name} data")
        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"Chemistry enrichment failed: {e}")
        return None


async def _enrich_from_memory(agent_type: AgentType, message: str) -> str | None:
    """Retrieve relevant past interactions from agent memory."""
    try:
        from app.graph.agent_memory import agent_memory

        context = await agent_memory.get_context_prompt(
            agent_type.value, message, max_chars=800
        )
        if context:
            return f"\n--- AGENT MEMORY ---\n{context}\n--- END MEMORY ---\n"
        return None

    except Exception:
        return None


async def save_interaction_memory(
    agent_type: AgentType,
    conversation_id: str,
    user_message: str,
    response_summary: str,
):
    """Save a summary of the interaction to agent memory for future context."""
    try:
        from app.graph.agent_memory import agent_memory

        # Generate a concise memory entry
        content = f"User asked: {user_message[:200]}. Response covered: {response_summary[:300]}"
        await agent_memory.add_memory(
            agent_type=agent_type.value,
            conversation_id=conversation_id,
            content=content,
            metadata={"agent": agent_type.value},
            memory_type="interaction",
        )
    except Exception as e:
        logger.debug(f"Memory save failed (non-critical): {e}")
