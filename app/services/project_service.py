"""Business rules for project workflow and Rev1 indicators."""

from datetime import UTC, date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.project import (
    PhaseHistoryEntity,
    PhaseHistoryUpdate,
    ProjectCreate,
    ProjectEntity,
    ProjectPhase,
    ProjectUpdate,
    allowed_next_phases,
)
from app.repositories.project_repository import ProjectRepository


class ProjectNotFoundError(Exception):
    pass


class PhaseHistoryNotFoundError(Exception):
    pass


class DuplicateProjectError(Exception):
    def __init__(self) -> None:
        super().__init__("Já existe um projeto com estes códigos e esta edição.")


class ProjectValidationError(Exception):
    def __init__(self, field: str, message: str) -> None:
        self.field = field
        super().__init__(message)


class InvalidTransitionError(Exception):
    def __init__(self, allowed: list[ProjectPhase]) -> None:
        self.allowed = allowed
        super().__init__("A fase de destino não é a próxima fase permitida.")


def calculate_indicators(
    selecionados: int, avisados: int, descartados: int
) -> tuple[int, int]:
    """Validate three strict inputs and return (Estoque, Executados)."""
    for name, value in (
        ("selecionados", selecionados),
        ("avisados", avisados),
        ("descartados", descartados),
    ):
        if type(value) is not int or value <= 0:
            raise ProjectValidationError(name, "Informe um número inteiro positivo.")
    if avisados > selecionados:
        raise ProjectValidationError(
            "avisados", "Avisados deve ser menor ou igual a Selecionados."
        )
    if descartados > avisados:
        raise ProjectValidationError(
            "descartados", "Descartados deve ser menor ou igual a Avisados."
        )
    return selecionados - avisados, avisados - descartados


def to_project_response(project: ProjectEntity) -> dict:
    return {
        "id": project.id,
        "codigo_projeto": project.codigo_projeto,
        "codigo_subprojeto": project.codigo_subprojeto,
        "titulo": project.titulo,
        "nome_subprojeto": project.nome_subprojeto,
        "edicao": project.edicao,
        "equipe": project.equipe,
        "data_prevista_execucao": project.data_prevista_execucao,
        "fase": project.fase,
        "data_inicio_fase": project.data_inicio_fase,
        "data_entrada_fase": project.data_entrada_fase,
        "selecionados": project.selecionados,
        "avisados": project.avisados,
        "descartados": project.descartados,
        "estoque": project.estoque,
        "executados": project.executados,
        "criado_em": project.criado_em,
        "atualizado_em": project.atualizado_em,
        "transicoes_permitidas": [
            phase.value for phase in allowed_next_phases(ProjectPhase(project.fase))
        ],
    }


class ProjectService:
    def __init__(self, session: Session) -> None:
        self.repository = ProjectRepository(session)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _is_duplicate_key_error(error: IntegrityError) -> bool:
        message = str(error.orig)
        return "UNIQUE constraint failed:" in message and all(
            f"projects.{field}" in message
            for field in ("codigo_projeto", "codigo_subprojeto", "edicao")
        )

    def _rollback_integrity_error(self, error: IntegrityError) -> None:
        self.repository.rollback()
        if self._is_duplicate_key_error(error):
            raise DuplicateProjectError() from error
        raise error

    def _ensure_unique(
        self, codigo_projeto: str, codigo_subprojeto: str, edicao: str,
        exclude_id: int | None = None,
    ) -> None:
        if self.repository.find_by_business_key(
            codigo_projeto, codigo_subprojeto, edicao, exclude_id=exclude_id
        ) is not None:
            raise DuplicateProjectError()

    @staticmethod
    def _require_current_event(project: ProjectEntity) -> PhaseHistoryEntity:
        if not project.historico or project.historico[-1].fase_destino != project.fase:
            raise ProjectValidationError(
                "historico", "O histórico da fase atual está inconsistente."
            )
        return project.historico[-1]

    def list_projects(self) -> list[ProjectEntity]:
        return list(self.repository.list())

    def get_project(self, project_id: int) -> ProjectEntity:
        project = self.repository.get(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Projeto {project_id} não encontrado.")
        return project

    def create_project(self, data: ProjectCreate) -> ProjectEntity:
        estoque, executados = calculate_indicators(
            data.selecionados, data.avisados, data.descartados
        )
        self._ensure_unique(
            data.codigo_projeto, data.codigo_subprojeto, data.edicao
        )
        now = self._now()
        phase_date = data.data_inicio_fase or now.date()
        try:
            project = self.repository.create(
                data, now, phase_date, estoque, executados
            )
            self.repository.commit()
            return project
        except IntegrityError as error:
            self._rollback_integrity_error(error)
        except Exception:
            self.repository.rollback()
            raise

    def update_project(self, project_id: int, changes: ProjectUpdate) -> ProjectEntity:
        project = self.get_project(project_id)
        current_event = self._require_current_event(project)
        values = changes.model_dump(exclude_unset=True)

        selecionados = values.get("selecionados", project.selecionados)
        avisados = values.get("avisados", project.avisados)
        descartados = values.get("descartados", project.descartados)
        estoque, executados = calculate_indicators(
            selecionados, avisados, descartados
        )

        codigo_projeto = values.get("codigo_projeto", project.codigo_projeto)
        codigo_subprojeto = values.get("codigo_subprojeto", project.codigo_subprojeto)
        edicao = values.get("edicao", project.edicao)
        self._ensure_unique(
            codigo_projeto, codigo_subprojeto, edicao, exclude_id=project.id
        )

        phase_date = values.get("data_inicio_fase", project.data_inicio_fase)
        if len(project.historico) > 1:
            previous_date = project.historico[-2].data_inicio_fase
            if phase_date < previous_date:
                raise ProjectValidationError(
                    "data_inicio_fase",
                    "A data não pode ser anterior à da fase precedente.",
                )

        try:
            updated = self.repository.update(
                project, current_event, values, self._now(), estoque, executados
            )
            self.repository.commit()
            return updated
        except IntegrityError as error:
            self._rollback_integrity_error(error)
        except Exception:
            self.repository.rollback()
            raise

    def change_phase(
        self, project_id: int, destination: ProjectPhase,
        data_inicio_fase: date | None = None,
    ) -> ProjectEntity:
        project = self.get_project(project_id)
        self._require_current_event(project)
        allowed = allowed_next_phases(ProjectPhase(project.fase))
        if destination not in allowed:
            raise InvalidTransitionError(allowed)

        now = self._now()
        phase_date = data_inicio_fase or now.date()
        if phase_date < project.data_inicio_fase or phase_date < now.date():
            raise ProjectValidationError(
                "data_inicio_fase",
                "A nova fase exige data igual ou posterior à fase anterior e ao dia UTC atual.",
            )
        try:
            updated = self.repository.change_phase(
                project, destination, phase_date, now
            )
            self.repository.commit()
            return updated
        except Exception:
            self.repository.rollback()
            raise

    def update_completed_phase(
        self, project_id: int, event_id: int, changes: PhaseHistoryUpdate
    ) -> PhaseHistoryEntity:
        project = self.get_project(project_id)
        self._require_current_event(project)
        events = project.historico
        index = next((i for i, item in enumerate(events) if item.id == event_id), None)
        if index is None:
            raise PhaseHistoryNotFoundError(
                f"Evento {event_id} não encontrado no projeto {project_id}."
            )
        if index == len(events) - 1:
            raise ProjectValidationError(
                "fase_destino", "A fase atual deve ser editada pelo PATCH do projeto."
            )

        event = events[index]
        values = changes.model_dump(exclude_unset=True)
        phase_date = values.get("data_inicio_fase", event.data_inicio_fase)
        previous_date = events[index - 1].data_inicio_fase if index > 0 else None
        next_date = events[index + 1].data_inicio_fase
        if (previous_date is not None and phase_date < previous_date) or (
            phase_date > next_date
        ):
            raise ProjectValidationError(
                "data_inicio_fase",
                "A data corrigida deve ficar entre as datas das fases vizinhas.",
            )

        counts = (
            values.get("selecionados", event.selecionados),
            values.get("avisados", event.avisados),
            values.get("descartados", event.descartados),
        )
        derived: tuple[int, int] | None = None
        if any(value is not None for value in counts):
            if any(value is None for value in counts):
                raise ProjectValidationError(
                    "selecionados",
                    "Informe as três contagens para completar esta fase histórica.",
                )
            derived = calculate_indicators(*counts)

        try:
            updated = self.repository.update_history(event, values, derived)
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
