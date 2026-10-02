"""SQLAlchemy persistence for projects and their phase history."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.project import (
    PHASE_ORDER,
    PhaseHistoryEntity,
    ProjectCreate,
    ProjectEntity,
    ProjectPhase,
    ProjectUpdate,
    allowed_next_phases,
)


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

    def create(
        self,
        data: ProjectCreate,
        now: datetime,
        conversion: Decimal | None,
    ) -> ProjectEntity:
        project = ProjectEntity(
            **data.model_dump(),
            fase=ProjectPhase.SELECAO.value,
            data_entrada_fase=now,
            criado_em=now,
            atualizado_em=now,
            taxa_conversao=conversion,
        )
        self.session.add(project)
        self.session.flush()
        # A criação registra a entrada inicial em Seleção; fase de origem é nula.
        self.session.add(PhaseHistoryEntity(
            projeto_id=project.id,
            fase_origem=None,
            fase_destino=ProjectPhase.SELECAO.value,
            alterado_em=now,
        ))
        return project

    def update(
        self,
        project: ProjectEntity,
        changes: ProjectUpdate,
        now: datetime,
        conversion: Decimal | None,
    ) -> ProjectEntity:
        for name, value in changes.model_dump(exclude_unset=True).items():
            setattr(project, name, value)
        project.taxa_conversao = conversion
        project.atualizado_em = now
        self.session.flush()
        return project

    def change_phase(
        self, project: ProjectEntity, destination: ProjectPhase, now: datetime
    ) -> ProjectEntity:
        origin = ProjectPhase(project.fase)
        project.fase = destination.value
        project.data_entrada_fase = now
        project.atualizado_em = now
        self.session.add(PhaseHistoryEntity(
            projeto_id=project.id,
            fase_origem=origin.value,
            fase_destino=destination.value,
            alterado_em=now,
        ))
        self.session.flush()
        return project

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
