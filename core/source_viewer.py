# core/source_viewer.py
#
# Inspector-pattern source viewer.
# Lightweight, stateful, typography-driven.

from __future__ import annotations

from pathlib import Path


def humanize_filename(filename: str) -> str:
    """
    Turn a filename into a clean display name.

    Q4_Revenue_2024.pdf   ->  Q4 Revenue 2024
    Vendor_Agreement_Final_v3.pdf  ->  Vendor Agreement Final V3
    contract-review.docx  ->  Contract Review
    """
    stem = Path(filename).stem
    stem = stem.replace("_", " ").replace("-", " ")
    return " ".join(stem.split()).title()


def get_active_source(citations: list, index: int) -> dict | None:
    """
    Return the citation dict at the given index, or None.
    Adds a computed 'display_name' field for presentation.
    """
    if not citations or index is None:
        return None
    if index < 0 or index >= len(citations):
        return None
    source = dict(citations[index])
    source["display_name"] = humanize_filename(source.get("filename", ""))
    return source


def render_source_panel(source: dict | None) -> str:
    """
    Return HTML for the inspector panel.

    If source is None, returns empty string.
    """
    if not source:
        return ""

    display_name = source.get("display_name", "Unknown")
    page = source.get("page", "?")
    snippet = source.get("snippet", "") or ""

    return f"""
    <div class="dockmind-inspector">
        <div class="dockmind-inspector-title">{display_name}</div>
        <div class="dockmind-inspector-page">p.{page}</div>
        <div class="dockmind-divider"></div>
        <div class="dockmind-inspector-excerpt">{snippet[:300]}</div>
    </div>
    """
