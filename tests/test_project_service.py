"""Rev1 contracts and service behavior, using isolated SQLite databases."""

from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import initialize_database
from app.models.project import (
    PhaseHistoryEntity, PhaseHistoryUpdate, ProjectCreate, ProjectEntity,
    ProjectPhase, ProjectUpdate,
)
from app.services.project_service import (
    DuplicateProjectError, InvalidTransitionError, ProjectService,
    ProjectValidationError, calculate_indicators,
)

NOW = datetime(2026, 10, 5, 12, tzinfo=UTC)
TODAY = NOW.date()


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    monkeypatch.setattr(ProjectService, "_now", staticmethod(lambda: NOW))


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    initialize_database(engine)
    try:
        with Session(engine, autoflush=False, expire_on_commit=False) as db:
            yield db
    finally:
        engine.dispose()


def create_data(**changes):
    values = dict(
        codigo_projeto="01.002", codigo_subprojeto="03", titulo="Projeto",
        nome_subprojeto="Subprojeto", edicao="2026", selecionados=10,
        avisados=8, descartados=3,
    )
    values.update(changes)
    return ProjectCreate(**values)


def snapshot(session):
    return [
        list(session.execute(select(entity.__table__)).mappings())
        for entity in (ProjectEntity, PhaseHistoryEntity)
    ]


def test_initial_phase_snapshot_and_optional_values(session):
    service = ProjectService(session)
    project = service.create_project(create_data())
    events = service.history(project.id)
    assert (project.codigo_projeto, project.codigo_subprojeto) == ("01.002", "03")
    assert project.equipe is None and project.data_prevista_execucao is None
    assert project.fase == "selecao" and project.data_inicio_fase == TODAY
    assert project.criado_em == project.atualizado_em == project.data_entrada_fase == NOW
    assert len(events) == 1
    assert (events[0].fase_origem, events[0].fase_destino) == (None, "selecao")
    assert events[0].alterado_em == NOW
    assert (events[0].selecionados, events[0].avisados, events[0].descartados) == (10, 8, 3)
    assert (events[0].estoque, events[0].executados) == (2, 5)


@pytest.mark.parametrize("values,expected", [
    ((10, 8, 3), (2, 5)), ((8, 8, 8), (0, 0)), ((10, 8, 8), (2, 0)),
])
def test_integer_indicators_and_zero(values, expected):
    result = calculate_indicators(*values)
    assert result == expected
    assert all(type(value) is int for value in result)


@pytest.mark.parametrize("position", range(3))
@pytest.mark.parametrize("invalid", [True, 1.5, "2", 0, -1])
def test_service_rejects_nonpositive_or_noninteger_inputs(position, invalid):
    counts = [10, 8, 3]
    counts[position] = invalid
    with pytest.raises(ProjectValidationError):
        calculate_indicators(*counts)


@pytest.mark.parametrize("field,limit", [
    ("titulo", 150), ("nome_subprojeto", 150), ("edicao", 30), ("equipe", 50),
])
def test_text_limits_and_trim(field, limit):
    assert getattr(create_data(**{field: " " + "x" * limit + " "}), field) == "x" * limit
    with pytest.raises(ValidationError):
        create_data(**{field: "x" * (limit + 1)})


@pytest.mark.parametrize("changes", [
    {"codigo_projeto": "1.002"}, {"codigo_projeto": "０１.002"},
    {"codigo_subprojeto": "3"}, {"codigo_subprojeto": "０３"},
    {"titulo": " "}, {"nome_subprojeto": ""}, {"edicao": " "},
    {"avisados": 11}, {"descartados": 9},
    {"data_prevista_execucao": "05/10/2026"},
    {"data_inicio_fase": None}, {"data_prevista_execucao": "2026-10-05T12:00:00Z"},
])
def test_invalid_contracts(changes):
    with pytest.raises(ValidationError):
        create_data(**changes)


def test_composite_key_case_and_duplicate_rollback(session):
    service = ProjectService(session)
    original = service.create_project(create_data(edicao="A"))
    service.create_project(create_data(codigo_subprojeto="04", edicao="A"))
    other = service.create_project(create_data(edicao="a"))
    before = snapshot(session)
    with pytest.raises(DuplicateProjectError):
        service.create_project(create_data(edicao="A"))
    with pytest.raises(DuplicateProjectError):
        service.update_project(other.id, ProjectUpdate(edicao="A"))
    assert snapshot(session) == before
    assert original.id != other.id


def test_patch_merges_state_recalculates_and_preserves_audit(session, monkeypatch):
    service = ProjectService(session)
    project = service.create_project(create_data())
    before = snapshot(session)
    with pytest.raises(ProjectValidationError):
        service.update_project(project.id, ProjectUpdate(selecionados=7, titulo="Invalid"))
    assert snapshot(session) == before
    monkeypatch.setattr(ProjectService, "_now", staticmethod(lambda: NOW + timedelta(hours=1)))
    updated = service.update_project(project.id, ProjectUpdate(
        selecionados=9, avisados=9, descartados=9, equipe="", data_prevista_execucao=None
    ))
    assert (updated.estoque, updated.executados) == (0, 0)
    assert updated.criado_em == updated.data_entrada_fase == NOW
    assert updated.atualizado_em == NOW + timedelta(hours=1)
    assert updated.fase == "selecao"
    event = service.history(project.id)[0]
    assert event.alterado_em == NOW
    assert (event.estoque, event.executados) == (0, 0)


def test_sequential_transitions_in_same_session_and_terminal_phase(session):
    service = ProjectService(session)
    project = service.create_project(create_data())
    for phase in list(ProjectPhase)[1:]:
        service.change_phase(project.id, phase)
    events = service.history(project.id)
    assert [event.fase_destino for event in events] == [phase.value for phase in ProjectPhase]
    assert [event.id for event in events] == sorted(event.id for event in events)
    assert project.fase == "encerrado"
    before = snapshot(session)
    with pytest.raises(InvalidTransitionError) as error:
        service.change_phase(project.id, ProjectPhase.SELECAO)
    assert error.value.allowed == []
    assert snapshot(session) == before


@pytest.mark.parametrize("phase", [
    ProjectPhase.SELECAO, ProjectPhase.EXECUCAO, ProjectPhase.ENCERRADO,
])
def test_skip_and_repeat_have_no_side_effects(session, phase):
    service = ProjectService(session)
    project = service.create_project(create_data())
    before = snapshot(session)
    with pytest.raises(InvalidTransitionError) as error:
        service.change_phase(project.id, phase)
    assert error.value.allowed == [ProjectPhase.DESENVOLVIMENTO]
    assert snapshot(session) == before


@pytest.mark.parametrize("initial,requested", [
    (TODAY - timedelta(days=2), TODAY - timedelta(days=1)),
    (TODAY + timedelta(days=2), TODAY + timedelta(days=1)),
])
def test_new_phase_must_follow_previous_and_current_day(session, initial, requested):
    service = ProjectService(session)
    project = service.create_project(create_data(data_inicio_fase=initial))
    before = snapshot(session)
    with pytest.raises(ProjectValidationError):
        service.change_phase(project.id, ProjectPhase.DESENVOLVIMENTO, requested)
    assert snapshot(session) == before


def test_historical_correction_between_neighbors_preserves_audit(session, monkeypatch):
    service = ProjectService(session)
    project = service.create_project(create_data(data_inicio_fase=TODAY - timedelta(days=2)))
    service.change_phase(project.id, ProjectPhase.DESENVOLVIMENTO, TODAY)
    service.change_phase(project.id, ProjectPhase.EXECUCAO, TODAY + timedelta(days=2))
    records = service.history(project.id)
    middle = records[1]
    before_project = snapshot(session)[0]
    audits = [event.alterado_em for event in records]
    monkeypatch.setattr(ProjectService, "_now", staticmethod(lambda: NOW + timedelta(days=20)))
    corrected = service.update_completed_phase(project.id, middle.id, PhaseHistoryUpdate(
        data_inicio_fase=TODAY + timedelta(days=1),
        titulo="Nome histórico", avisados=8, descartados=8,
    ))
    assert corrected.titulo == "Nome histórico"
    assert corrected.executados == 0
    assert snapshot(session)[0] == before_project
    assert [event.alterado_em for event in service.history(project.id)] == audits
    for invalid in [TODAY - timedelta(days=3), TODAY + timedelta(days=3)]:
        before = snapshot(session)
        with pytest.raises(ProjectValidationError):
            service.update_completed_phase(
                project.id, middle.id, PhaseHistoryUpdate(data_inicio_fase=invalid)
            )
        assert snapshot(session) == before
    with pytest.raises(ProjectValidationError):
        service.update_completed_phase(project.id, records[-1].id, PhaseHistoryUpdate(titulo="X"))


def test_current_phase_date_cannot_precede_previous(session):
    service = ProjectService(session)
    project = service.create_project(create_data())
    service.change_phase(project.id, ProjectPhase.DESENVOLVIMENTO)
    before = snapshot(session)
    with pytest.raises(ProjectValidationError):
        service.update_project(
            project.id, ProjectUpdate(data_inicio_fase=TODAY - timedelta(days=1))
        )
    assert snapshot(session) == before


def test_delete_cascades_all_history(session):
    service = ProjectService(session)
    project = service.create_project(create_data())
    service.change_phase(project.id, ProjectPhase.DESENVOLVIMENTO)
    service.delete_project(project.id)
    assert snapshot(session) == [[], []]


@pytest.mark.parametrize("operation", ["create", "update", "phase", "history", "delete"])
def test_flushed_writes_roll_back_atomically(session, monkeypatch, operation):
    service = ProjectService(session)
    project = service.create_project(create_data())
    service.change_phase(project.id, ProjectPhase.DESENVOLVIMENTO)
    first_event = service.history(project.id)[0]
    before = snapshot(session)
    original_flush = session.flush

    def fail_after_flush(*args, **kwargs):
        original_flush(*args, **kwargs)
        raise RuntimeError("injected failure after flush")

    monkeypatch.setattr(session, "flush", fail_after_flush)
    actions = {
        "create": lambda: service.create_project(create_data(edicao="Outra")),
        "update": lambda: service.update_project(project.id, ProjectUpdate(titulo="Changed")),
        "phase": lambda: service.change_phase(project.id, ProjectPhase.EXECUCAO),
        "history": lambda: service.update_completed_phase(
            project.id, first_event.id, PhaseHistoryUpdate(titulo="Changed history")
        ),
        "delete": lambda: service.delete_project(project.id),
    }
    with pytest.raises(RuntimeError, match="injected failure"):
        actions[operation]()
    monkeypatch.setattr(session, "flush", original_flush)
    session.expire_all()
    assert snapshot(session) == before


@pytest.mark.parametrize("changes", [
    {"codigo_projeto": "1.002"}, {"codigo_subprojeto": "A3"}, {"titulo": " "},
    {"nome_subprojeto": "x" * 151}, {"edicao": "x" * 31}, {"equipe": "x" * 51},
    {"selecionados": 0}, {"avisados": 11}, {"descartados": 9},
    {"estoque": 99}, {"executados": 99},
])
def test_database_constraints_reject_invalid_writes(session, changes):
    service = ProjectService(session)
    project = service.create_project(create_data())
    before = snapshot(session)
    with pytest.raises(IntegrityError):
        session.execute(update(ProjectEntity).where(ProjectEntity.id == project.id).values(**changes))
        session.commit()
    session.rollback()
    assert snapshot(session) == before


def test_project_and_history_survive_engine_restart(tmp_path):
    path = tmp_path / "persist.db"
    engine = create_engine(f"sqlite:///{path}")
    initialize_database(engine)
    with Session(engine, expire_on_commit=False) as db:
        service = ProjectService(db)
        project = service.create_project(create_data(data_prevista_execucao=date(2026, 11, 1)))
        service.change_phase(project.id, ProjectPhase.DESENVOLVIMENTO)
        project_id = project.id
        before = snapshot(db)
    engine.dispose()
    reopened = create_engine(f"sqlite:///{path}")
    try:
        initialize_database(reopened)
        with Session(reopened) as db:
            assert snapshot(db) == before
            restored = ProjectService(db).get_project(project_id)
            assert (restored.estoque, restored.executados) == (2, 5)
            assert restored.data_prevista_execucao == date(2026, 11, 1)
            assert restored.criado_em.tzinfo == UTC
    finally:
        reopened.dispose()
