# core/ui_design_system.py
#
# The Source of Truth for DocMind's Brutalist Editorial Design System.
# Typography-first. Monochrome. Information-dense.
#
from __future__ import annotations

# ── Design Tokens ──────────────────────────────────────────────────────────────
TOKENS = {
    "colors": {
        "bg": "#0A0A0A",
        "surface": "#141414",
        "text": "#FFFFFF",
        "secondary": "#A1A1AA",
        "border": "#27272A",
        "accent": "#3B82F6",
    },
    "fonts": {
        "display": "'Space Grotesk', sans-serif",
        "body": "'Inter', sans-serif",
        "mono": "'IBM Plex Mono', monospace",
    },
    "spacing": {
        "gutter": "24px",
        "section": "4rem",
        "block": "2rem",
    }
}

# ── Global CSS Framework ──────────────────────────────────────────────────────
# All styles are strictly scoped under #brutalist-root to prevent leakage.
CSS_STYLES = f"""
#brutalist-root {{
    --bg-color: {TOKENS['colors']['bg']};
    --surface-color: {TOKENS['colors']['surface']};
    --text-color: {TOKENS['colors']['text']};
    --secondary-color: {TOKENS['colors']['secondary']};
    --border-color: {TOKENS['colors']['border']};
    --accent-color: {TOKENS['colors']['accent']};
    --font-display: {TOKENS['fonts']['display']};
    --font-body: {TOKENS['fonts']['body']};
    --font-mono: {TOKENS['fonts']['mono']};
}}

/* ── Root Reset ── */
#brutalist-root div,
#brutalist-root p,
#brutalist-root span,
#brutalist-root button,
#brutalist-root input,
#brutalist-root textarea,
#brutalist-root label,
#brutalist-root form {{
    box-sizing: border-box;
}}

#brutalist-root .stApp {{
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
}}

#brutalist-root section[data-testid="stSidebar"] {{
    background-color: var(--bg-color) !important;
    border-right: 1px solid var(--border-color) !important;
}}

/* ── Typography ── */
#brutalist-root .editorial-title {{
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1.75rem;
    line-height: 1.2;
    color: var(--text-color);
    margin-bottom: 2rem;
    letter-spacing: -0.01em;
}}

#brutalist-root .editorial-label {{
    font-family: var(--font-mono);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--secondary-color);
    margin-bottom: 0.75rem;
    display: block;
    font-weight: 600;
    opacity: 0.6;
}}

/* ── Layout ── */
#brutalist-root .dockmind-canvas {{
    max-width: 820px;
    margin: 0 auto;
    padding: 0 32px;
    font-family: var(--font-body);
}}

/* ── Chat Rhythm ── */
#brutalist-root .msg-wrapper {{
    margin-bottom: 2rem;
}}

#brutalist-root .msg-user {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    text-align: right;
    width: 65%;
    margin-left: auto;
    padding: 1rem 0;
    border-right: 2px solid var(--border-color);
    font-weight: 500;
    color: var(--text-color);
    font-size: 1rem;
    line-height: 1.55;
}}

#brutalist-root .msg-assistant {{
    display: block;
    background-color: transparent;
    border-top: 1px solid var(--border-color);
    padding: 1.5rem 0;
    width: 100%;
    color: var(--text-color);
    line-height: 1.65;
    font-size: 1rem;
}}

/* ── Reading Experience ── */
#brutalist-root .msg-assistant p {{
    margin-bottom: 1.1rem;
    line-height: 1.7;
}}

#brutalist-root .msg-assistant p:last-child {{
    margin-bottom: 0;
}}

#brutalist-root .msg-assistant ul,
#brutalist-root .msg-assistant ol {{
    margin-bottom: 1.1rem;
    padding-left: 1.5rem;
}}

#brutalist-root .msg-assistant li {{
    margin-bottom: 0.5rem;
    line-height: 1.6;
}}

#brutalist-root .msg-assistant li:last-child {{
    margin-bottom: 0;
}}

#brutalist-root .msg-assistant blockquote {{
    margin: 1rem 0;
    padding: 0.5rem 1rem;
    border-left: 2px solid var(--border-color);
    color: var(--secondary-color);
    font-style: italic;
}}

#brutalist-root .msg-assistant hr {{
    border: none;
    border-top: 1px solid var(--border-color);
    margin: 2rem 0;
}}

#brutalist-root .msg-assistant pre {{
    background-color: var(--surface-color);
    border: 1px solid var(--border-color);
    padding: 1rem 1.25rem;
    overflow-x: auto;
    margin: 1rem 0;
    border-radius: 0;
}}

#brutalist-root .msg-assistant code {{
    font-family: var(--font-mono);
    font-size: 0.85rem;
    line-height: 1.5;
    color: var(--text-color);
}}

#brutalist-root .msg-assistant p code {{
    background-color: rgba(255,255,255,0.04);
    padding: 0.15rem 0.4rem;
    border-radius: 2px;
}}

#brutalist-root .msg-assistant pre code {{
    background-color: transparent;
    padding: 0;
    border-radius: 0;
}}

#brutalist-root .msg-assistant table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
    overflow-x: auto;
    display: block;
}}

#brutalist-root .msg-assistant th,
#brutalist-root .msg-assistant td {{
    padding: 0.6rem 0.75rem;
    border: 1px solid var(--border-color);
    text-align: left;
    line-height: 1.5;
    font-size: 0.9rem;
}}

#brutalist-root .msg-assistant th {{
    font-weight: 600;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background-color: rgba(255,255,255,0.02);
}}

#brutalist-root .msg-assistant td {{
    font-family: var(--font-body);
}}

#brutalist-root .msg-assistant td[align="right"],
#brutalist-root .msg-assistant th[align="right"] {{
    text-align: right;
    font-family: var(--font-mono);
    font-size: 0.85rem;
}}

/* ── Citations (Editorial Panel) ── */
#brutalist-root .sources-panel {{
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-color);
}}

#brutalist-root .source-item {{
    font-family: var(--font-body);
    font-size: 0.9rem;
    padding: 0.6rem 0;
    color: var(--secondary-color);
    border-bottom: 1px solid rgba(255,255,255,0.04);
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 1rem;
    cursor: default;
    transition: color 0.15s ease;
}}

#brutalist-root .source-item:hover {{
    color: var(--text-color);
}}

#brutalist-root .source-item:last-child {{
    border-bottom: none;
}}

#brutalist-root .source-filename {{
    color: var(--text-color);
    font-weight: 500;
    font-size: 0.9rem;
}}

#brutalist-root .source-page {{
    font-family: var(--font-mono);
    font-size: 0.8rem;
    opacity: 0.6;
    white-space: nowrap;
}}

#brutalist-root .source-snippet {{
    font-family: var(--font-body);
    font-size: 0.85rem;
    color: var(--secondary-color);
    margin-top: 0.35rem;
    line-height: 1.5;
    opacity: 0;
    max-height: 0;
    overflow: hidden;
    transition: opacity 0.2s ease, max-height 0.2s ease;
}}

#brutalist-root .source-item:hover .source-snippet {{
    opacity: 1;
    max-height: 6rem;
}}

/* ── Editorial Design System ── */
#brutalist-root .dockmind-section {{
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.15em;
    font-weight: 600;
    opacity: 0.45;
    text-transform: uppercase;
    margin-top: 2rem;
    margin-bottom: 0.75rem;
    padding: 0 0.5rem;
    user-select: none;
}}

#brutalist-root .dockmind-item {{
    font-family: var(--font-body);
    font-size: 14px;
    font-weight: 500;
    padding: 0.4rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    transition: opacity 0.15s ease;
    color: var(--text-color);
    opacity: 1;
}}

#brutalist-root .dockmind-item:hover {{
    opacity: 0.75;
}}

#brutalist-root .dockmind-item.active {{
    font-weight: 600;
    opacity: 1;
    background: rgba(255,255,255,0.06);
}}

#brutalist-root .dockmind-meta {{
    font-family: var(--font-body);
    font-size: 12px;
    opacity: 0.5;
    padding: 0 0.5rem;
    line-height: 1.3;
}}

#brutalist-root .dockmind-ghost {{
    background: none;
    border: none;
    color: var(--text-color);
    opacity: 0;
    font-size: 12px;
    cursor: pointer;
    padding: 2px 6px;
    transition: opacity 0.15s ease;
}}

#brutalist-root .dockmind-item:hover .dockmind-ghost {{
    opacity: 1;
}}

#brutalist-root .dockmind-ghost:hover {{
    opacity: 1;
}}

#brutalist-root .dockmind-workspace {{
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 500;
    opacity: 0.7;
    padding: 0.25rem 0.5rem;
}}

#brutalist-root .dockmind-divider {{
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 1rem 0;
}}

#brutalist-root .dockmind-link {{
    background: none;
    border: none;
    color: var(--secondary-color);
    font-size: 13px;
    padding: 0.35rem 0.5rem;
    cursor: pointer;
    opacity: 0.8;
    text-align: left;
}}

#brutalist-root .dockmind-link:hover {{
    opacity: 1;
    color: var(--text-color);
}}

#brutalist-root .dockmind-spacer-bottom {{
    margin-bottom: 0.5rem;
}}

#brutalist-root .dockmind-spacer-top {{
    margin-top: 0.5rem;
}}

#brutalist-root .dockmind-faded {{
    opacity: 0.4;
}}

#brutalist-root .auth-center {{
    text-align: center;
    margin-top: 100px;
}}

#brutalist-root .empty-state {{
    text-align: center;
    margin-top: 100px;
    color: var(--secondary-color);
    opacity: 0.6;
    font-family: var(--font-body);
    font-size: 0.95rem;
    line-height: 1.6;
}}
#brutalist-root .typing-indicator {{
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--secondary-color);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: flex;
    align-items: center;
    gap: 4px;
    opacity: 0.7;
}}

#brutalist-root .blink {{
    animation: blinker 0.8s linear infinite;
}}

@keyframes blinker {{
    50% {{ opacity: 0; }}
}}

/* Auth Screen */
#brutalist-root .auth-title {{
    font-family: var(--font-display);
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--text-color);
    margin-bottom: 0.5rem;
    letter-spacing: -0.01em;
}}

#brutalist-root .auth-subtitle {{
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--secondary-color);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    opacity: 0.6;
    margin-bottom: 3rem;
}}

#brutalist-root .auth-center {{
    text-align: center;
    margin-top: 100px;
}}

#brutalist-root .empty-state {{
    text-align: center;
    margin-top: 100px;
    color: var(--secondary-color);
    opacity: 0.6;
    font-family: var(--font-body);
    font-size: 0.95rem;
    line-height: 1.6;
}}

/* ── Inspector Panel ── */
#brutalist-root .dockmind-inspector {{
    background: #0D0D0D;
    border-left: 1px solid var(--border-color);
    padding: 1.5rem;
    font-family: var(--font-body);
}}

#brutalist-root .dockmind-inspector-title {{
    font-family: var(--font-display);
    font-size: 14px;
    font-weight: 500;
    color: var(--text-color);
    margin-bottom: 0.25rem;
    line-height: 1.3;
}}

#brutalist-root .dockmind-inspector-page {{
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--secondary-color);
    opacity: 0.6;
    margin-bottom: 1.25rem;
}}

#brutalist-root .dockmind-inspector-divider {{
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 1rem 0;
}}

#brutalist-root .dockmind-inspector-excerpt {{
    font-family: var(--font-body);
    font-size: 14px;
    line-height: 1.6;
    color: var(--text-color);
}}
"""
