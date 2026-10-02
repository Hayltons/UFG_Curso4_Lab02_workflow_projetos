"""REST endpoints for project records and phase history."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import PhaseChange, PhaseHistoryOut, ProjectCreate, ProjectOut, ProjectUpdate
from app.services.project_service import (
    InvalidTransitionError,
    ProjectNotFoundError,
    ProjectService,
    to_project_response,
)

router = APIRouter(prefix="/projects", tags=["projects"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def service(session: DatabaseSession) -> ProjectService:
    return ProjectService(session)


@router.get("", response_model=list[ProjectOut])
def list_projects(projects: ProjectService = Depends(service)) -> list[dict]:
    return [to_project_response(item) for item in projects.list_projects()]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, projects: ProjectService = Depends(service)) -> dict:
    return to_project_response(projects.create_project(data))


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, projects: ProjectService = Depends(service)) -> dict:
    try:
        return to_project_response(projects.get_project(project_id))
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int, data: ProjectUpdate, projects: ProjectService = Depends(service)
) -> dict:
    try:
        return to_project_response(projects.update_project(project_id, data))
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, projects: ProjectService = Depends(service)) -> Response:
    try:
        projects.delete_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/phase", response_model=ProjectOut)
def change_phase(
    project_id: int, data: PhaseChange, projects: ProjectService = Depends(service)
) -> dict:
    try:
        return to_project_response(projects.change_phase(project_id, data.fase))
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "transicoes_permitidas": [phase.value for phase in exc.allowed],
            },
        ) from exc


@router.get("/{project_id}/history", response_model=list[PhaseHistoryOut])
def get_history(project_id: int, projects: ProjectService = Depends(service)) -> list:
    try:
        return projects.history(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
