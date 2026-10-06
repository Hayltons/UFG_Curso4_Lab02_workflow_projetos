"""REST endpoints for Rev1 projects and phase history."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import (
    PhaseChange,
    PhaseHistoryOut,
    PhaseHistoryUpdate,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
)
from app.services.project_service import (
    DuplicateProjectError,
    InvalidTransitionError,
    PhaseHistoryNotFoundError,
    ProjectNotFoundError,
    ProjectService,
    ProjectValidationError,
    to_project_response,
)

router = APIRouter(prefix="/projects", tags=["projects"])
DatabaseSession = Annotated[Session, Depends(get_db)]

_CREATE_EXAMPLES = {
    "rev1": {
        "summary": "Cadastro Rev1",
        "value": {
            "codigo_projeto": "01.234",
            "codigo_subprojeto": "01",
            "titulo": "Projeto Exemplo",
            "nome_subprojeto": "Subprojeto Exemplo",
            "edicao": "2026",
            "equipe": "Equipe A",
            "selecionados": 10,
            "avisados": 8,
            "descartados": 8,
        },
    }
}
_UPDATE_EXAMPLES = {
    "contagens": {
        "summary": "Atualização parcial das contagens",
        "value": {"avisados": 9, "descartados": 9},
    },
    "limpar_previsao": {
        "summary": "Limpar data opcional",
        "value": {"data_prevista_execucao": None},
    },
}
_PHASE_EXAMPLES = {
    "proxima_fase": {
        "summary": "Avançar para a próxima fase",
        "value": {"fase": "desenvolvimento"},
    }
}
_HISTORY_EXAMPLES = {
    "corrigir_fase_concluida": {
        "summary": "Corrigir data e equipe de uma fase concluída",
        "value": {"data_inicio_fase": "2026-10-04", "equipe": "Equipe A"},
    }
}


def service(session: DatabaseSession) -> ProjectService:
    return ProjectService(session)


def _not_found(error: ProjectNotFoundError | PhaseHistoryNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


def _duplicate(error: DuplicateProjectError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "fields": ["codigo_projeto", "codigo_subprojeto", "edicao"],
            "message": str(error),
        },
    )


def _invalid_data(error: ProjectValidationError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"field": error.field, "message": str(error)},
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(projects: ProjectService = Depends(service)) -> list[dict]:
    return [to_project_response(item) for item in projects.list_projects()]


@router.post(
    "", response_model=ProjectOut, status_code=status.HTTP_201_CREATED,
    description="Cria um projeto na fase Seleção. Estoque e Executados são calculados.",
)
def create_project(
    data: Annotated[ProjectCreate, Body(openapi_examples=_CREATE_EXAMPLES)],
    projects: ProjectService = Depends(service),
) -> dict:
    try:
        return to_project_response(projects.create_project(data))
    except DuplicateProjectError as exc:
        raise _duplicate(exc) from exc
    except ProjectValidationError as exc:
        raise _invalid_data(exc) from exc


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, projects: ProjectService = Depends(service)) -> dict:
    try:
        return to_project_response(projects.get_project(project_id))
    except ProjectNotFoundError as exc:
        raise _not_found(exc) from exc


@router.patch(
    "/{project_id}", response_model=ProjectOut,
    description="Edita campos do projeto sem mudar a fase ou a auditoria UTC.",
)
def update_project(
    project_id: int,
    data: Annotated[ProjectUpdate, Body(openapi_examples=_UPDATE_EXAMPLES)],
    projects: ProjectService = Depends(service),
) -> dict:
    try:
        return to_project_response(projects.update_project(project_id, data))
    except ProjectNotFoundError as exc:
        raise _not_found(exc) from exc
    except DuplicateProjectError as exc:
        raise _duplicate(exc) from exc
    except ProjectValidationError as exc:
        raise _invalid_data(exc) from exc


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, projects: ProjectService = Depends(service)) -> Response:
    try:
        projects.delete_project(project_id)
    except ProjectNotFoundError as exc:
        raise _not_found(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/phase", response_model=ProjectOut,
    description="Avança somente à fase seguinte; a data sugerida é o dia UTC atual.",
)
def change_phase(
    project_id: int,
    data: Annotated[PhaseChange, Body(openapi_examples=_PHASE_EXAMPLES)],
    projects: ProjectService = Depends(service),
) -> dict:
    try:
        return to_project_response(
            projects.change_phase(project_id, data.fase, data.data_inicio_fase)
        )
    except ProjectNotFoundError as exc:
        raise _not_found(exc) from exc
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "transicoes_permitidas": [phase.value for phase in exc.allowed],
            },
        ) from exc
    except ProjectValidationError as exc:
        raise _invalid_data(exc) from exc


@router.get("/{project_id}/history", response_model=list[PhaseHistoryOut])
def get_history(project_id: int, projects: ProjectService = Depends(service)) -> list:
    try:
        return projects.history(project_id)
    except ProjectNotFoundError as exc:
        raise _not_found(exc) from exc


@router.patch(
    "/{project_id}/history/{event_id}", response_model=PhaseHistoryOut,
    description=(
        "Corrige campos de negócio de uma fase concluída, inclusive a data, "
        "sem alterar identidade, sequência ou horários UTC de auditoria."
    ),
)
def update_completed_phase(
    project_id: int,
    event_id: int,
    data: Annotated[PhaseHistoryUpdate, Body(openapi_examples=_HISTORY_EXAMPLES)],
    projects: ProjectService = Depends(service),
) -> PhaseHistoryOut:
    try:
        return projects.update_completed_phase(project_id, event_id, data)
    except (ProjectNotFoundError, PhaseHistoryNotFoundError) as exc:
        raise _not_found(exc) from exc
    except ProjectValidationError as exc:
        raise _invalid_data(exc) from exc
