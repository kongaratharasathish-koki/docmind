# core/document_comparator.py
#
# Responsible for performing a deep comparative analysis between two PDF documents.
#
# Design notes:
#   - Extracts full text from both documents to ensure a holistic comparison.
#   - Uses a structured, multi-dimensional prompt to force Gemini to analyze
#     across several specific axes (Similarities, Differences, Contradictions, etc.).
#   - Returns a structured dictionary for clean rendering in the UI.
#
from __future__ import annotations

import re
from typing import List, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI

import config
from core.pdf_processor import extract_text_from_pdf

def compare_documents(file1_bytes: bytes, name1: str, file2_bytes: bytes, name2: str) -> Dict[str, Any]:
    """
    Perform a comprehensive comparison between two PDF documents.

    Args:
        file1_bytes: bytes of the first PDF.
        name1: filename of the first PDF.
        file2_bytes: bytes of the second PDF.
        name2: filename of the second PDF.

    Returns:
        A dictionary containing the comparative analysis sections.
    """
    # ── 1. Extract text from both documents ──────────────────────────────────
    def get_full_text(bytes_data, filename):
        pages = extract_text_from_pdf(bytes_data, filename)
        return "\n\n".join([p["text"] for p in pages])

    text1 = get_full_text(file1_bytes, name1)
    text2 = get_full_text(file2_bytes, name2)

    if not text1.strip() or not text2.strip():
        raise ValueError("One or both of the selected documents contains no extractable text.")

    # ── 2. Generate comparative analysis with Gemini ─────────────────────────
    llm = ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.2,
        convert_system_message_to_human=True,
    )

    prompt = (
        "You are an expert document analyst. Compare the two provided documents "
        "and provide a highly structured comparative analysis. "
        "The output must be divided into exactly these 7 sections, each starting "
        "with the specified header:\n\n"
        "1. EXECUTIVE SUMMARY: A high-level overview of how the two documents relate.\n"
        "2. KEY SIMILARITIES: Bullet points of shared concepts, goals, or data.\n"
        "3. KEY DIFFERENCES: Bullet points of where the documents diverge in approach or content.\n"
        "4. MISSING INFORMATION: What is present in Document A but missing in B, and vice versa.\n"
        "5. CONTRADICTIONS: Direct conflicts or opposing claims between the two documents.\n"
        "6. SIDE-BY-SIDE ANALYSIS: A structured comparison of key themes (e.g., Theme X: Doc A says... while Doc B says...).\n"
        "7. ACTIONABLE INSIGHTS: Recommendations or conclusions based on this comparison.\n\n"
        "DOCUMENT A (" + name1 + "):\n"
        "-------------------\n"
        f"{text1}\n"
        "-------------------\n\n"
        "DOCUMENT B (" + name2 + "):\n"
        "-------------------\n"
        f"{text2}\n"
        "-------------------"
    )

    response = llm.invoke(prompt)
    content = response.content

    # ── 3. Parse response into structured dict ────────────────────────────────
    sections = {
        "executive_summary": "N/A",
        "similarities": "N/A",
        "differences": "N/A",
        "missing_info": "N/A",
        "contradictions": "N/A",
        "side_by_side": "N/A",
        "insights": "N/A"
    }

    patterns = {
        "executive_summary": r"EXECUTIVE SUMMARY:(.*?)(?=\n\nKEY SIMILARITIES:|\Z)",
        "similarities": r"KEY SIMILARITIES:(.*?)(?=\n\nKEY DIFFERENCES:|\Z)",
        "differences": r"KEY DIFFERENCES:(.*?)(?=\n\nMISSING INFORMATION:|\Z)",
        "missing_info": r"MISSING INFORMATION:(.*?)(?=\n\nCONTRADICTIONS:|\Z)",
        "contradictions": r"CONTRADICTIONS:(.*?)(?=\n\nSIDE-BY-SIDE ANALYSIS:|\Z)",
        "side_by_side": r"SIDE-BY-SIDE ANALYSIS:(.*?)(?=\n\nACTIONABLE INSIGHTS:|\Z)",
        "insights": r"ACTIONABLE INSIGHTS:(.*)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()

    return sections
