# DocMind — AI Document Assistant

A production-grade AI assistant that lets you chat across multiple PDFs, built with Python · FastAPI · Flutter · Gemini.

## Pricing (USD)

| Plan | Price | Features |
|------|-------|----------|
| Student | $4.99/month | 5 libraries, 50 documents, basic support |
| Research Assistant | $9.99/month | 20 libraries, 500 documents, priority support |
| Professional | $19.99/month | Unlimited libraries/documents, priority support |
| Business | $49.99/month | Multi-user, API access, dedicated support |

## Quick start (Backend)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Gemini API key in .env
cp .env.example .env

# 3. Run FastAPI backend
uvicorn app.main:app --reload
```

## Project structure

```
DocMind/
├── app/                 # FastAPI backend
│   ├── routers/         # /auth, /libraries, /sessions, /upload, /chat, /search, /analytics
│   ├── services/        # Business logic layer
│   ├── middleware/      # Rate limiting, logging
│   └── schemas.py       # Pydantic models
├── core/                # AI brain + utilities
│   ├── chat_engine.py   # LangChain ConversationalRetrievalChain
│   ├── vectorstore_manager.py  # FAISS + embeddings
│   ├── pdf_processor.py # PDF extraction
│   └── payment_config.py # Pricing in USD
├── config/              # Configuration
└── requirements.txt
```

## Features

| Feature | Status |
|---------|--------|
| Multi-PDF support | ✅ Done |
| PDF summarization | ✅ Done |
| Citation support | ✅ Done |
| Chat history persistence | ✅ Done |
| Document comparison | ✅ Done |
| PDF export | ✅ Done |
| JWT authentication | ✅ Done |
| Rate limiting | ✅ Done |
| Structured logging | ✅ Done |
| RESTful API (FastAPI) | ✅ Done |
| Payment integration (USD) | ✅ Config ready |
