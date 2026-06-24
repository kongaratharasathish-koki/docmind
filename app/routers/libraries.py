# app/routers/libraries.py

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import LibraryCreate, LibraryResponse
from app.deps import get_current_user
from app.services import library_service

router = APIRouter(prefix="/libraries", tags=["libraries"])


@router.get("", response_model=list[LibraryResponse])
def get_libraries(current_user: dict = Depends(get_current_user)):
    return library_service.list_libraries(current_user["user_id"])


@router.post("", response_model=LibraryResponse)
def create_library(payload: LibraryCreate, current_user: dict = Depends(get_current_user)):
    return library_service.create_library(current_user["user_id"], payload.name)


@router.delete("/{library_id}")
def delete_library(library_id: int, current_user: dict = Depends(get_current_user)):
    archived = library_service.delete_library(current_user["user_id"], library_id)
    if not archived:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library not found or access denied",
        )
    return {"detail": "Library archived"}
