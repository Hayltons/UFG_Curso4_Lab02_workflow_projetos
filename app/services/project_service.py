"""Business rules for project workflow and indicators."""

from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models.project import (
    PhaseHistoryEntity,
    ProjectCreate,
    ProjectEntity,
    ProjectPhase,
    ProjectUpdate,
    allowed_next_phases,
)
from app.repositories.project_repository import ProjectRepository


class ProjectNotFoundError(Exception):
    pass


class InvalidTransitionError(Exception):
    def __init__(self, allowed: list[ProjectPhase]) -> None:
        self.allowed = allowed
        super().__init__("A fase de destino não é a próxima fase permitida.")


def conversion_rate(targets: int, customers: int) -> Decimal | None:
    """Calculate percent and round half-up to two decimals; zero targets -> None."""
    if targets == 0:
        return None
    return (Decimal(customers) * Decimal(100) / Decimal(targets)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def to_project_response(project: ProjectEntity) -> dict:
    return {
        "id": project.id,
        "titulo": project.titulo,
        "descricao": project.descricao,
        "equipe": project.equipe,
        "fase": project.fase,
        "data_entrada_fase": project.data_entrada_fase,
        "alvos_planejados": project.alvos_planejados,
        "clientes_sensibilizados": project.clientes_sensibilizados,
        "indice_satisfacao": project.indice_satisfacao,
        "taxa_conversao": project.taxa_conversao,
        "criado_em": project.criado_em,
        "atualizado_em": project.atualizado_em,
        "transicoes_permitidas": [phase.value for phase in allowed_next_phases(ProjectPhase(project.fase))],
    }


class ProjectService:
    def __init__(self, session: Session) -> None:
        self.repository = ProjectRepository(session)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def list_projects(self) -> list[ProjectEntity]:
        return list(self.repository.list())

    def get_project(self, project_id: int) -> ProjectEntity:
        project = self.repository.get(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Projeto {project_id} não encontrado.")
        return project

    def create_project(self, data: ProjectCreate) -> ProjectEntity:
        now = self._now()
        conversion = conversion_rate(data.alvos_planejados, data.clientes_sensibilizados)
        try:
            project = self.repository.create(data, now, conversion)
            self.repository.commit()
            return project
        except Exception:
            self.repository.rollback()
            raise

    def update_project(self, project_id: int, changes: ProjectUpdate) -> ProjectEntity:
        project = self.get_project(project_id)
        values = changes.model_dump(exclude_unset=True)
        targets = values.get("alvos_planejados", project.alvos_planejados)
        customers = values.get("clientes_sensibilizados", project.clientes_sensibilizados)
        conversion = conversion_rate(targets, customers)
        try:
            updated = self.repository.update(project, changes, self._now(), conversion)
            self.repository.commit()
            return updated
        except Exception:
            self.repository.rollback()
            raise

    def change_phase(self, project_id: int, destination: ProjectPhase) -> ProjectEntity:
        project = self.get_project(project_id)
        origin = ProjectPhase(project.fase)
        allowed = allowed_next_phases(origin)
        if destination not in allowed:
            raise InvalidTransitionError(allowed)
        try:
            updated = self.repository.change_phase(project, destination, self._now())
            self.repository.commit()
            return updated
        except Exception:
            self.repository.rollback()
            raise

    def history(self, project_id: int) -> list[PhaseHistoryEntity]:
        self.get_project(project_id)
        return list(self.repository.history(project_id))

    def delete_project(self, project_id: int) -> None:
        project = self.get_project(project_id)
        try:
            self.repository.delete(project)
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise
