"""Analysis template API routes.

Endpoints (all require authentication):
  GET    /templates              — List current user's templates
  POST   /templates              — Create a new template
  GET    /templates/{id}         — Get one of the user's templates
  PATCH  /templates/{id}         — Update a template
  DELETE /templates/{id}         — Delete a template
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.auth.models import User
from app.modules.templates.schemas import (
    CreateTemplateRequest,
    TemplateListResponse,
    TemplateResponse,
    UpdateTemplateRequest,
)
from app.modules.templates.service import TemplateService

router = APIRouter(prefix="/templates", tags=["Templates"])


def _get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> TemplateService:
    return TemplateService(session=db)


@router.get(
    "",
    summary="List my templates",
    description="List the authenticated user's analysis templates, newest first.",
    response_model=TemplateListResponse,
)
async def list_templates(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TemplateService, Depends(_get_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TemplateListResponse:
    return await service.list_templates(
        user.id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a template",
    description="Save a reusable analysis template for the authenticated user.",
    response_model=TemplateResponse,
)
async def create_template(
    body: CreateTemplateRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TemplateService, Depends(_get_service)],
) -> TemplateResponse:
    try:
        return await service.create_template(body, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/{template_id}",
    summary="Get a template",
    description="Fetch one of the authenticated user's templates.",
    response_model=TemplateResponse,
)
async def get_template(
    template_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TemplateService, Depends(_get_service)],
) -> TemplateResponse:
    result = await service.get_template(template_id, user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.patch(
    "/{template_id}",
    summary="Update a template",
    description="Partially update one of the authenticated user's templates.",
    response_model=TemplateResponse,
)
async def update_template(
    template_id: uuid.UUID,
    body: UpdateTemplateRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TemplateService, Depends(_get_service)],
) -> TemplateResponse:
    try:
        result = await service.update_template(template_id, body, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a template",
    description="Delete one of the authenticated user's templates.",
)
async def delete_template(
    template_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TemplateService, Depends(_get_service)],
) -> None:
    deleted = await service.delete_template(template_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
