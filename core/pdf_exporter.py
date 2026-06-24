# core/pdf_exporter.py
#
# Responsible for generating a professional PDF report of the
# AI Document Assistant's output.
#
# Design notes:
#   - Uses reportlab's Platypus for high-level layout and multi-page support.
#   - Processes chat history by stripping HTML tags used for UI styling.
#   - Implements a consistent professional style with headers and sectioning.
#
from __future__ import annotations

import io
from datetime import datetime
from typing import List, Dict, Any

from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

def generate_pdf_report(
    processed_files: List[str],
    summary: Dict[str, Any],
    chat_history: List[Dict[str, str]]
) -> io.BytesIO:
    """
    Generates a professional PDF report containing documents,
    summaries, and chat history.

    Returns:
        A BytesIO object containing the PDF data.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()

    # ── Custom Styles ──────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.hexColor("#3b5bdb")
    )
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        textColor=colors.hexColor("#1e2535"),
        borderPadding=5,
    )
    body_style = styles['Normal']
    body_style.fontSize = 11
    body_style.leading = 14

    story = []

    # ── 1. Title Page ───────────────────────────────────────────────────────
    story.append(Spacer(1, 100))
    story.append(Paragraph("DocMind Analysis Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Confidential Document Analysis", body_style))
    story.append(PageBreak())

    # ── 2. Document Context ─────────────────────────────────────────────────
    story.append(Paragraph("Analyzed Documents", header_style))
    if processed_files:
        doc_list = [f"📄 {f}" for f in processed_files]
        # Simple list as a table for clean alignment
        data = [[item] for item in doc_list]
        t = Table(data, colWidths=[400])
        t.setStyle(TableStyle([
            ('TEXT', (0, 0), (-1, -1), body_style),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No documents were processed.", body_style))
    story.append(Spacer(1, 20))

    # ── 3. Executive Summary ────────────────────────────────────────────────
    if summary:
        story.append(Paragraph("Executive Summary", header_style))

        # Short Summary
        story.append(Paragraph("<b>Short Summary:</b>", body_style))
        story.append(Paragraph(summary.get("short_summary", "N/A"), body_style))
        story.append(Spacer(1, 12))

        # Detailed Summary
        story.append(Paragraph("<b>Detailed Analysis:</b>", body_style))
        story.append(Paragraph(summary.get("detailed_summary", "N/A"), body_style))
        story.append(Spacer(1, 12))

        # Key Points
        story.append(Paragraph("<b>Key Points:</b>", body_style))
        points = summary.get("key_points", "N/A")
        story.append(Paragraph(points.replace("\\n", "<br/>"), body_style))
        story.append(Spacer(1, 12))

        # Action Items
        story.append(Paragraph("<b>Action Items:</b>", body_style))
        actions = summary.get("action_items", "N/A")
        story.append(Paragraph(actions.replace("\\n", "<br/>"), body_style))
        story.append(Spacer(1, 20))
    else:
        story.append(Paragraph("No summary generated.", body_style))
        story.append(Spacer(1, 20))

    # ── 4. Chat Transcript ──────────────────────────────────────────────────
    story.append(Paragraph("Interaction Transcript", header_style))

    if chat_history:
        for msg in chat_history:
            role = msg["role"].capitalize()
            content = msg["content"]

            # Strip HTML tags (like <div> and <span>) for PDF
            import re
            clean_content = re.sub(r'<[^>]*>', '', content)

            # Format role as a bold header
            story.append(Paragraph(f"<b>{role}:</b>", body_style))
            story.append(Paragraph(clean_content, body_style))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("No chat history available.", body_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
