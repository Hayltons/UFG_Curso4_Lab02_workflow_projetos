"""SQLAlchemy persistence for Rev1 projects and phase history."""

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.project import (
    PHASE_ORDER,
    PhaseHistoryEntity,
    ProjectCreate,
    ProjectEntity,
    ProjectPhase,
    allowed_next_phases,
)


_BUSINESS_FIELDS = (
    "codigo_projeto",
    "codigo_subprojeto",
    "titulo",
    "nome_subprojeto",
    "edicao",
    "equipe",
    "data_prevista_execucao",
    "selecionados",
    "avisados",
    "descartados",
    "estoque",
    "executados",
)


def _snapshot(project: ProjectEntity) -> dict:
    """Copy known business values into the event for the current phase."""
    return {name: getattr(project, name) for name in _BUSINESS_FIELDS}


class ProjectRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> Sequence[ProjectEntity]:
        statement = select(ProjectEntity).order_by(ProjectEntity.id)
        return self.session.scalars(statement).all()

    def get(self, project_id: int) -> ProjectEntity | None:
        statement = (
            select(ProjectEntity)
            .options(selectinload(ProjectEntity.historico))
            .where(ProjectEntity.id == project_id)
        )
        return self.session.scalar(statement)

    def find_by_business_key(
        self, codigo_projeto: str, codigo_subprojeto: str, edicao: str,
        exclude_id: int | None = None,
    ) -> ProjectEntity | None:
        statement = select(ProjectEntity).where(
            ProjectEntity.codigo_projeto == codigo_projeto,
            ProjectEntity.codigo_subprojeto == codigo_subprojeto,
            ProjectEntity.edicao == edicao,
        )
        if exclude_id is not None:
            statement = statement.where(ProjectEntity.id != exclude_id)
        return self.session.scalar(statement.limit(1))

    def create(
        self, data: ProjectCreate, now: datetime, phase_date: date,
        estoque: int, executados: int,
    ) -> ProjectEntity:
        project = ProjectEntity(
            **data.model_dump(exclude={"data_inicio_fase"}),
            fase=ProjectPhase.SELECAO.value,
            data_inicio_fase=phase_date,
            data_entrada_fase=now,
            estoque=estoque,
            executados=executados,
            criado_em=now,
            atualizado_em=now,
        )
        self.session.add(project)
        self.session.flush()
        initial_event = PhaseHistoryEntity(
            projeto_id=project.id,
            fase_origem=None,
            fase_destino=ProjectPhase.SELECAO.value,
            data_inicio_fase=phase_date,
            alterado_em=now,
            **_snapshot(project),
        )
        project.historico.append(initial_event)
        self.session.flush()
        return project

    def update(
        self, project: ProjectEntity, current_event: PhaseHistoryEntity,
        values: dict, now: datetime, estoque: int, executados: int,
    ) -> ProjectEntity:
        for name, value in values.items():
            setattr(project, name, value)
        project.estoque = estoque
        project.executados = executados
        project.atualizado_em = now

        # A fase corrente mirrors the editable business state; the audit time
        # of its entry remains unchanged.
        for name, value in _snapshot(project).items():
            setattr(current_event, name, value)
        current_event.data_inicio_fase = project.data_inicio_fase

        self.session.flush()
        return project

    def change_phase(
        self, project: ProjectEntity, destination: ProjectPhase,
        phase_date: date, now: datetime,
    ) -> ProjectEntity:
        origin = ProjectPhase(project.fase)
        project.fase = destination.value
        project.data_inicio_fase = phase_date
        project.data_entrada_fase = now
        project.atualizado_em = now
        event = PhaseHistoryEntity(
            projeto_id=project.id,
            fase_origem=origin.value,
            fase_destino=destination.value,
            data_inicio_fase=phase_date,
            alterado_em=now,
            **_snapshot(project),
        )
        project.historico.append(event)
        self.session.flush()
        return project

    def update_history(
        self, event: PhaseHistoryEntity, values: dict,
        derived: tuple[int, int] | None,
    ) -> PhaseHistoryEntity:
        for name, value in values.items():
            setattr(event, name, value)
        if derived is not None:
            event.estoque, event.executados = derived
        # Identity, phase sequence and all UTC audit timestamps are untouched.
        self.session.flush()
        return event

    def history(self, project_id: int) -> Sequence[PhaseHistoryEntity]:
        statement = (
            select(PhaseHistoryEntity)
            .where(PhaseHistoryEntity.projeto_id == project_id)
            .order_by(PhaseHistoryEntity.alterado_em, PhaseHistoryEntity.id)
        )
        return self.session.scalars(statement).all()

    def delete(self, project: ProjectEntity) -> None:
        # Delete dependents explicitly so cascade semantics hold on every SQL backend.
        self.session.execute(
            delete(PhaseHistoryEntity).where(PhaseHistoryEntity.projeto_id == project.id)
        )
        self.session.expire(project, ["historico"])
        self.session.delete(project)
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()


def next_phases(phase: ProjectPhase) -> list[ProjectPhase]:
    """Expose only immediate sequential transitions to the API/UI."""
    return allowed_next_phases(phase)


def phase_sequence() -> tuple[ProjectPhase, ...]:
    return PHASE_ORDER
