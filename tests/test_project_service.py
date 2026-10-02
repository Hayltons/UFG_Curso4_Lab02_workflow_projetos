from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.project import (
    PhaseHistoryEntity,
    ProjectCreate,
    ProjectEntity,
    ProjectPhase,
    ProjectUpdate,
)
from app.services.project_service import (
    InvalidTransitionError,
    ProjectService,
    conversion_rate,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        yield db
    Base.metadata.drop_all(engine)
    engine.dispose()


def create_data(**changes):
    values = {"titulo": "Projeto", "equipe": "Equipe A"}
    values.update(changes)
    return ProjectCreate(**values)


def test_new_project_starts_in_selection_and_records_initial_history(session):
    service = ProjectService(session)
    project = service.create_project(create_data())
    events = service.history(project.id)
    assert project.fase == ProjectPhase.SELECAO.value
    assert project.data_entrada_fase == events[0].alterado_em
    assert len(events) == 1
    assert events[0].fase_origem is None
    assert events[0].fase_destino == ProjectPhase.SELECAO.value
    assert project.fase == ProjectPhase.SELECAO.value


def test_only_immediate_next_phase_is_allowed(session):
    service = ProjectService(session)
    project = service.create_project(create_data())
    updated = service.change_phase(project.id, ProjectPhase.DESENVOLVIMENTO)
    assert updated.fase == "desenvolvimento"
    events = service.history(project.id)
    assert [(e.fase_origem, e.fase_destino) for e in events] == [
        (None, "selecao"), ("selecao", "desenvolvimento")
    ]
    assert updated.data_entrada_fase == events[-1].alterado_em


@pytest.mark.parametrize("phase", [ProjectPhase.EXECUCAO, ProjectPhase.ENCERRADO, ProjectPhase.SELECAO])
def test_rejects_skip_repeat_or_reopen_without_history_change(session, phase):
    service = ProjectService(session)
    project = service.create_project(create_data())
    before_date = project.data_entrada_fase
    with pytest.raises(InvalidTransitionError) as error:
        service.change_phase(project.id, phase)
    assert error.value.allowed == [ProjectPhase.DESENVOLVIMENTO]
    session.expire_all()
    refreshed = service.get_project(project.id)
    assert refreshed.fase == "selecao"
    assert refreshed.data_entrada_fase == before_date
    assert len(service.history(project.id)) == 1


def test_encerrado_is_terminal(session):
    service = ProjectService(session)
    project = service.create_project(create_data())
    for phase in list(ProjectPhase)[1:]:
        project = service.change_phase(project.id, phase)
    assert project.fase == "encerrado"
    assert len(service.history(project.id)) == 5
    with pytest.raises(InvalidTransitionError) as error:
        service.change_phase(project.id, ProjectPhase.SELECAO)
    assert error.value.allowed == []
    assert len(service.history(project.id)) == 5


def test_conversion_rounds_half_up_to_two_places():
    assert conversion_rate(800, 1) == Decimal("0.13")
    assert conversion_rate(6, 1) == Decimal("16.67")


def test_zero_targets_has_no_conversion_and_above_one_hundred_is_allowed(session):
    service = ProjectService(session)
    no_targets = service.create_project(create_data(clientes_sensibilizados=4))
    above = service.create_project(create_data(titulo="Acima", alvos_planejados=2, clientes_sensibilizados=5))
    assert no_targets.taxa_conversao is None
    assert above.taxa_conversao == Decimal("250.00")


def test_update_recalculates_conversion_and_satisfaction(session):
    service = ProjectService(session)
    project = service.create_project(create_data(alvos_planejados=4, clientes_sensibilizados=1))
    updated = service.update_project(project.id, ProjectUpdate(
        alvos_planejados=3, clientes_sensibilizados=2, indice_satisfacao=9.5
    ))
    assert updated.taxa_conversao == Decimal("66.67")
    assert updated.indice_satisfacao == 9.5
    assert updated.fase == "selecao"


def test_project_delete_cascades_history(session):
    service = ProjectService(session)
    project = service.create_project(create_data())
    service.change_phase(project.id, ProjectPhase.DESENVOLVIMENTO)
    service.delete_project(project.id)
    assert session.scalar(select(func.count()).select_from(ProjectEntity)) == 0
    assert session.scalar(select(func.count()).select_from(PhaseHistoryEntity)) == 0


def test_phase_and_history_roll_back_together_on_write_failure(session, monkeypatch):
    service = ProjectService(session)
    project = service.create_project(create_data())
    original_phase = project.fase

    original_flush = session.flush

    def fail_after_phase_and_history_are_staged(*_args, **_kwargs):
        raise RuntimeError("database write failed")

    monkeypatch.setattr(session, "flush", fail_after_phase_and_history_are_staged)
    with pytest.raises(RuntimeError, match="database write failed"):
        service.change_phase(project.id, ProjectPhase.DESENVOLVIMENTO)
    monkeypatch.setattr(session, "flush", original_flush)
    session.expire_all()
    assert session.get(ProjectEntity, project.id).fase == original_phase
    assert session.scalar(select(func.count()).select_from(PhaseHistoryEntity)) == 1


def test_create_validates_satisfaction_and_nonnegative_counts():
    with pytest.raises(ValueError):
        create_data(indice_satisfacao=10.1)
    with pytest.raises(ValueError):
        create_data(indice_satisfacao=-0.1)
    with pytest.raises(ValueError):
        create_data(alvos_planejados=-1)
    with pytest.raises(ValueError):
        create_data(clientes_sensibilizados=-1)


def test_project_and_history_survive_database_restart(tmp_path):
    database_path = tmp_path / "persist.db"
    first_engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(first_engine)
    with Session(first_engine, expire_on_commit=False) as first_session:
        service = ProjectService(first_session)
        project = service.create_project(create_data(alvos_planejados=5, clientes_sensibilizados=2))
        service.change_phase(project.id, ProjectPhase.DESENVOLVIMENTO)
        project_id = project.id
    first_engine.dispose()

    reopened_engine = create_engine(f"sqlite:///{database_path}")
    with Session(reopened_engine) as reopened_session:
        service = ProjectService(reopened_session)
        restored = service.get_project(project_id)
        events = service.history(project_id)
        assert restored.fase == "desenvolvimento"
        assert restored.taxa_conversao == Decimal("40.00")
        assert len(events) == 2
        assert events[-1].fase_destino == "desenvolvimento"
    reopened_engine.dispose()
