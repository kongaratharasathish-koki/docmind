# core/pdf_processor.py
#
# Responsible for ONE thing: turning a list of uploaded PDF file objects
# into a searchable FAISS vector store.
#
# Design notes:
#   - Each chunk is tagged with its source filename so future citation
#     support (Feature #3) can retrieve provenance without extra work.
#   - The function is stateless — it receives files, returns a retriever.
#     The caller (app.py) decides how long to cache it.

from __future__ import annotations

import io
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pypdf import PdfReader

import config


def extract_text_from_pdf(file_bytes: bytes, filename: str) -> List[dict]:
    """
    Read raw bytes of a PDF and return a list of page dicts:
        {"text": str, "source": filename, "page": int}
    """
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if text:  # skip blank/image-only pages
            pages.append({
                "text": text,
                "source": filename,
                "page": page_num,
            })
    return pages


def build_vector_store(uploaded_files) -> FAISS:
    """
    Accept a list of Streamlit UploadedFile objects, extract text from all
    of them, split into overlapping chunks, embed with Google's embedding
    model, and return a FAISS vector store.

    Args:
        uploaded_files: list[UploadedFile]  — from st.file_uploader

    Returns:
        FAISS vector store ready for similarity search.

    Raises:
        ValueError: if no text could be extracted from any of the files.
    """
    if not uploaded_files:
        raise ValueError("No files provided.")

    # ── 1. Extract raw text from every PDF ───────────────────────────────────
    all_pages: List[dict] = []
    for uf in uploaded_files:
        file_bytes = uf.read()
        pages = _extract_text_from_pdf(file_bytes, uf.name)
        all_pages.extend(pages)

    if not all_pages:
        raise ValueError(
            "Could not extract text from any uploaded file. "
            "Make sure the PDFs contain selectable text (not just scanned images)."
        )

    # ── 2. Split pages into overlapping chunks ────────────────────────────────
    # RecursiveCharacterTextSplitter tries to split on paragraph → sentence →
    # word boundaries before hard-cutting at chunk_size, which keeps chunks
    # semantically cleaner than a naive character split.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    from langchain.schema import Document

    documents: List[Document] = []
    for page in all_pages:
        chunks = splitter.split_text(page["text"])
        for chunk in chunks:
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": page["source"],
                        "page": page["page"],
                    },
                )
            )

    # ── 3. Embed and index ────────────────────────────────────────────────────
    embeddings = GoogleGenerativeAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        google_api_key=config.GEMINI_API_KEY,
    )
    vector_store = FAISS.from_documents(documents, embeddings)
    return vector_store


def get_retriever(vector_store: FAISS):
    """
    Wrap the FAISS store in a LangChain retriever.
    Extracted as a separate function so the retriever config (k, search type)
    can be changed in one place without touching the rest of the pipeline.
    """
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": config.TOP_K_DOCS},
    )
