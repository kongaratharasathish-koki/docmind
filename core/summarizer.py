# core/summarizer.py
#
# Responsible for generating multi-faceted summaries of uploaded documents.
#
# Design notes:
#   - Extracts full text from all provided PDFs to ensure the summary
#     is holistic and not just based on retrieved chunks (RAG).
#   - Uses a structured prompt to force Gemini to return the four specific
#     sections required by the product specification.
#
from __future__ import annotations

from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI

import config
from core.pdf_processor import _extract_text_from_pdf

def summarize_documents(uploaded_files: List) -> dict:
    """
    Extract text from all uploaded PDFs and generate a comprehensive
    summary consisting of: Short Summary, Detailed Summary, Key Points, and Action Items.

    Args:
        uploaded_files: list of Streamlit UploadedFile objects.

    Returns:
        A dictionary containing the four summary sections.
    """
    if not uploaded_files:
        raise ValueError("No files provided for summarization.")

    # ── 1. Extract all text ───────────────────────────────────────────────────
    full_text = []
    for uf in uploaded_files:
        # Reset file pointer to beginning in case it was read elsewhere
        uf.seek(0)
        file_bytes = uf.read()
        pages = _extract_text_from_pdf(file_bytes, uf.name)
        for page in pages:
            full_text.append(page["text"])

    combined_text = "\n\n".join(full_text)

    if not combined_text.strip():
        raise ValueError("Could not extract any text from the uploaded PDFs.")

    # ── 2. Generate summary with Gemini ─────────────────────────────────────────
    llm = ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.3,
        convert_system_message_to_human=True,
    )

    prompt = (
        "You are a professional document analyst. Please analyze the following text "
        "extracted from one or more documents and provide a comprehensive summary "
        "structured exactly into these four sections:\n\n"
        "1. SHORT SUMMARY: A concise 2-3 sentence overview of the main topic.\n"
        "2. DETAILED SUMMARY: A thorough explanation of the core arguments, findings, or content.\n"
        "3. KEY POINTS: A bulleted list of the most important facts or takeaways.\n"
        "4. ACTION ITEMS: A bulleted list of recommended next steps, tasks, or deliverables identified in the text.\n\n"
        "If any section is not applicable based on the text, state 'Not applicable'.\n\n"
        "TEXT TO ANALYZE:\n"
        "-------------------\n"
        f"{combined_text}"
        "\n-------------------"
    )

    response = llm.invoke(prompt)
    content = response.content

    # ── 3. Parse response into structured dict ──────────────────────────────────
    # Since we've asked for a specific format, we can split by the section headers.
    sections = {
        "short_summary": "",
        "detailed_summary": "",
        "key_points": "",
        "action_items": ""
    }

    # Simple parsing based on known headers
    try:
        parts = content.split("\n\n")
        for part in parts:
            if "SHORT SUMMARY:" in part.upper():
                sections["short_summary"] = part.replace("SHORT SUMMARY:", "").strip()
            elif "DETAILED SUMMARY:" in part.upper():
                sections["detailed_summary"] = part.replace("DETAILED SUMMARY:", "").strip()
            elif "KEY POINTS:" in part.upper():
                sections["key_points"] = part.replace("KEY POINTS:", "").strip()
            elif "ACTION ITEMS:" in part.upper():
                sections["action_items"] = part.replace("ACTION ITEMS:", "").strip()
    except Exception:
        # Fallback: just put the whole thing in detailed summary
        sections["detailed_summary"] = content

    # If parsing failed to find specific sections, we can return the whole content
    # in the detailed summary and leave others empty, or try a more robust split.
    # Let's refine the parsing to be slightly more robust.

    import re
    patterns = {
        "short_summary": r"SHORT SUMMARY:(.*?)(?=\n\nDETAILED SUMMARY:|\Z)",
        "detailed_summary": r"DETAILED SUMMARY:(.*?)(?=\n\nKEY POINTS:|\Z)",
        "key_points": r"KEY POINTS:(.*?)(?=\n\nACTION ITEMS:|\Z)",
        "action_items": r"ACTION ITEMS:(.*)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()

    return sections
