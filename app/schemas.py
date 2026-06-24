# app/schemas.py
#
# Shared Pydantic models for request/response contracts.

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr


class UserSignup(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class EmailOnly(BaseModel):
    model_config = {"extra": "forbid"}
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class LibraryCreate(BaseModel):
    name: str


class LibraryResponse(BaseModel):
    id: int
    name: str
    archived_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    document_count: int = 0

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    name: Optional[str] = None
    library_id: Optional[int] = None


class SessionResponse(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    library_id: Optional[int] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: int
    question: str


class CitationResponse(BaseModel):
    filename: str
    page: int
    chunk: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: List[CitationResponse] = []


class SearchRequest(BaseModel):
    query: str
    library_id: Optional[int] = None


class SearchResponse(BaseModel):
    collections: List[Dict[str, Any]] = []
    sessions: List[Dict[str, Any]] = []
    messages: List[Dict[str, Any]] = []
    documents: List[Dict[str, Any]] = []


class AnalyticsResponse(BaseModel):
    total_documents: int
    total_libraries: int
    total_sessions: int
    total_messages: int
    top_library: Optional[Dict[str, Any]] = None
    last_active: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True
