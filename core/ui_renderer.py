# core/ui_renderer.py
#
# Responsible for transforming raw data into Brutalist Editorial HTML.
# Implements a secure, high-performance markdown rendering pipeline with
# Streamlit-native caching for production stability.
#
from __future__ import annotations

import streamlit as st
import markdown
import bleach
from typing import Dict, Any

# Define allowed HTML tags for the markdown pipeline to prevent XSS
ALLOWED_TAGS = [
    'p', 'b', 'i', 'strong', 'em', 'ul', 'ol', 'li', 'br', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'blockquote', 'hr'
]
ALLOWED_ATTRS = {
    'span': ['class', 'style'],
    'div': ['class', 'style'],
    'th': ['align'],
    'td': ['align'],
}

# Version identifier to force cache invalidation when rendering rules change
RENDER_VERSION = "1.3.0"

@st.cache_data(show_spinner=False)
def _process_markdown_to_html(content: str, version: str, tags: tuple, attrs: tuple) -> str:
    """
    Secure rendering pipeline:
    1. Sanitize raw input (remove all HTML/scripts)
    2. Convert clean markdown -> HTML
    3. Apply final bleach sanitization on the output.

    The 'version' parameter and config tuples ensure that any update to the
    design system or security rules invalidates the cache globally.
    """
    # Step 1: Remove any raw HTML from the input to prevent markdown injection
    # This ensures the markdown parser handles only pure text.
    stripped_input = bleach.clean(content, tags=[], strip=True)

    # Step 2: Convert clean markdown to HTML with table + code block support
    raw_html = markdown.markdown(stripped_input, extensions=['tables', 'fenced_code', 'nl2br'])

    # Step 3: Final safety layer - sanitize the generated HTML
    # Note: we cast tags/attrs to lists because bleach expects lists, not tuples.
    return bleach.clean(
        raw_html,
        tags=list(tags),
        attributes=dict(attrs),
        strip=True
    )

def render_message(role: str, content: str) -> str:
    """
    Wraps chat content in the la professional editorial layout.
    Utilizes the secure cached pipeline for content processing.

    Args:
        role: "user" or "assistant"
        content: The message text
    Returns:
        HTML string for the message block.
    """
    # Pass version and config to the cached function to ensure cache correctness.
    # Tuples are used instead of lists because st.cache_data requires hashable arguments.
    safe_content = _process_markdown_to_html(
        content,
        RENDER_VERSION,
        tuple(ALLOWED_TAGS),
        tuple(ALLOWED_ATTRS.items())
    )

    if role == "user":
        return f"""
        <div class="msg-wrapper">
            <div class="msg-user">
                {safe_content}
            </div>
        </div>
        """

    # Assistant messages are treated as a structured "insight" block
    return f"""
    <div class="msg-wrapper">
        <div class="msg-assistant">
            <span class="editorial-label">Insight Engine</span>
            <div style="margin-top: 1rem;">
                {safe_content}
            </div>
        </div>
    </div>
    """

def render_typing_indicator() -> str:
    """Returns the HTML for the blinking terminal-style thinking state."""
    return """
    <div class="typing-indicator">
        GENERATING INSIGHT<span class="blink">_</span}
    </div>
    """

def render_citations(citations: list) -> None:
    """
    Render citations as a clean editorial panel beneath the conversation.
    No pills. No emojis. Typography only.
    
    Args:
        citations: List of citation dictionaries with filename, page, chunk, and snippet
    """
    if not citations:
        return
    
    st.markdown('<div class="dockmind-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="dockmind-section">Sources</div>', unsafe_allow_html=True)
    
    for idx, citation in enumerate(citations):
        filename = citation.get("filename", "Unknown File")
        page = citation.get("page", "Unknown Page")
        chunk = citation.get("chunk", idx + 1)
        snippet = citation.get("snippet", "") or ""
        
        st.markdown(f'''
        <div class="source-item">
            <div>
                <span class="source-filename">{filename}</span>
                <div class="source-snippet">{snippet[:220]}</div>
            </div>
            <span class="source-page">p.{page}</span>
        </div>
        ''', unsafe_allow_html=True)
