# core/citations.py
#
# Responsible for processing and formatting source citations from
# LangChain documents.
#
# Design notes:
#   - Deduplicates citations to avoid showing the same page multiple times.
#   - Formats metadata (source, page) into human-readable strings.
#   - Decoupled from Streamlit UI components, returning data structures
#     that the UI layer can render.
#
from __future__ import annotations

from typing import List, Set
from langchain.schema import Document

def _extract_snippet(text: str, max_length: int = 250) -> str:
    """
    Extract a clean snippet of 200-300 characters, preserving sentence boundaries.
    
    Args:
        text: Source text to extract from
        max_length: Maximum character length (default 250, within 200-300 range)
    
    Returns:
        Cleaned excerpt string
    """
    if not text:
        return ""
    
    # Strip excessive whitespace and line breaks
    cleaned = " ".join(text.split())
    
    if len(cleaned) <= max_length:
        return cleaned
    
    # Try to find sentence boundary near max_length
    for i in range(max_length, max_length - 50, -1):
        if i < len(cleaned) and cleaned[i] in '.!?':
            return cleaned[:i + 1]
    
    # Fallback: find space to avoid cutting words
    for i in range(max_length, max_length - 30, -1):
        if i < len(cleaned) and cleaned[i] == ' ':
            return cleaned[:i]
    
    # Last fallback: hard truncate
    return cleaned[:max_length]

def format_citations(source_docs: List[Document]) -> List[dict]:
    """
    Process a list of source documents and return a unique, sorted list of
    citations containing filename, page, chunk, and excerpt snippet.

    Args:
        source_docs: List of LangChain Document objects used for the answer.

    Returns:
        A list of dictionaries, each containing 'filename', 'page', 'chunk', and 'snippet'.
    """
    if not source_docs:
        return []

    unique_sources: Set[tuple] = set()
    ordered_citations = []

    for i, doc in enumerate(source_docs):
        meta = doc.metadata
        source = meta.get("source", "Unknown File")
        raw_page = meta.get("page", 0)
        # Coerce page to int when possible. LangChain metadata may carry
        # a string for indexed sources, or "Unknown Page" if missing.
        try:
            page = int(raw_page)
        except (TypeError, ValueError):
            page = 0
        chunk_id = i + 1

        # Extract snippet from page content
        snippet = _extract_snippet(doc.page_content) if doc.page_content else ""

        citation_tuple = (source, page)
        if citation_tuple not in unique_sources:
            unique_sources.add(citation_tuple)
            ordered_citations.append({
                "filename": source,
                "page": page,
                "chunk": chunk_id,
                "snippet": snippet
            })

    return ordered_citations
