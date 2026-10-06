"""HTTP contracts of Rev1; TestClient uses a temporary database and no TCP server."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.main as main_module
from app.database import get_db
from app.services.project_service import ProjectService

NOW = datetime(2026, 10, 5, 12, tzinfo=UTC)


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'api-test.db'}", connect_args={"check_same_thread": False}
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(main_module, "engine", engine)
    monkeypatch.setattr(ProjectService, "_now", staticmethod(lambda: NOW))

    def override_get_db():
        with testing_session() as session:
            yield session

    previous = main_module.app.dependency_overrides.copy()
    main_module.app.dependency_overrides[get_db] = override_get_db
    try:
        # Lifespan creates/version-checks this test database, never projects.db.
        with TestClient(main_module.app) as test_client:
            yield test_client
    finally:
        main_module.app.dependency_overrides.clear()
        main_module.app.dependency_overrides.update(previous)
        engine.dispose()


def payload(**overrides):
    body = dict(
        codigo_projeto="01.002", codigo_subprojeto="03", titulo="Projeto",
        nome_subprojeto="Subprojeto", edicao="2026", selecionados=10,
        avisados=8, descartados=3,
    )
    body.update(overrides)
    return body


def create(client, **overrides):
    response = client.post("/projects", json=payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def state(client, project_id):
    return (
        client.get(f"/projects/{project_id}").json(),
        client.get(f"/projects/{project_id}/history").json(),
    )


def test_health_empty_list_and_openapi(client):
    health = client.get("/health")
    assert health.status_code == 200 and health.json()["status"] == "ok"
    assert health.json()["version"] == main_module.APP_VERSION
    assert datetime.fromisoformat(health.json()["timestamp"].replace("Z", "+00:00")).tzinfo == UTC
    assert client.get("/projects").json() == []
    schema = client.get("/openapi.json").json()
    assert schema["info"]["version"] == health.json()["version"]
    assert "patch" in schema["paths"]["/projects/{project_id}"]
    assert "put" not in schema["paths"]["/projects/{project_id}"]
    assert "patch" in schema["paths"]["/projects/{project_id}/history/{event_id}"]
    inputs = schema["components"]["schemas"]["ProjectCreate"]["properties"]
    assert "selecionados" in inputs
    assert not {"estoque", "executados", "criado_em", "indice_satisfacao"} & inputs.keys()


def test_create_list_detail_initial_history_and_integer_zero(client):
    project = create(client, selecionados=8, avisados=8, descartados=8)
    assert project["codigo_projeto"] == "01.002" and project["codigo_subprojeto"] == "03"
    assert project["equipe"] is None and project["data_prevista_execucao"] is None
    assert project["fase"] == "selecao" and project["data_inicio_fase"] == "2026-10-05"
    assert project["estoque"] == project["executados"] == 0
    assert type(project["estoque"]) is int and type(project["executados"]) is int
    assert project["transicoes_permitidas"] == ["desenvolvimento"]
    assert not {"descricao", "taxa_conversao", "indice_satisfacao"} & project.keys()
    detail, history = state(client, project["id"])
    assert detail == project and client.get("/projects").json() == [project]
    assert len(history) == 1
    assert (history[0]["fase_origem"], history[0]["fase_destino"]) == (None, "selecao")
    assert history[0]["alterado_em"] == project["data_entrada_fase"]
    assert history[0]["executados"] == 0
    assert project["criado_em"].endswith("Z")


@pytest.mark.parametrize("field", [
    "codigo_projeto", "codigo_subprojeto", "titulo", "nome_subprojeto", "edicao",
])
def test_required_fields_missing_and_blank(client, field):
    body = payload()
    del body[field]
    assert client.post("/projects", json=body).status_code == 422
    assert client.post("/projects", json=payload(**{field: " "})).status_code == 422
    assert client.get("/projects").json() == []


@pytest.mark.parametrize("field", ["selecionados", "avisados", "descartados"])
@pytest.mark.parametrize("invalid", [True, False, 1.5, "2", 0, -1])
def test_counts_are_strict_positive_integers(client, field, invalid):
    response = client.post("/projects", json=payload(**{field: invalid}))
    assert response.status_code == 422
    assert client.get("/projects").json() == []


@pytest.mark.parametrize("changes", [
    {"avisados": 11}, {"descartados": 9},
    {"codigo_projeto": "1.002"}, {"codigo_projeto": "٠١.002"},
    {"codigo_subprojeto": "3"}, {"codigo_subprojeto": "０３"},
    {"titulo": "x" * 151}, {"nome_subprojeto": "x" * 151},
    {"edicao": "x" * 31}, {"equipe": "x" * 51},
    {"data_prevista_execucao": "05/10/2026"}, {"data_prevista_execucao": "2026-02-30"},
    {"data_prevista_execucao": 123}, {"data_prevista_execucao": "2026-10-05T00:00:00Z"},
    {"data_inicio_fase": None},
])
def test_invalid_create_has_no_side_effects(client, changes):
    assert client.post("/projects", json=payload(**changes)).status_code == 422
    assert client.get("/projects").json() == []


def test_maximum_lengths_trimming_optional_dates_and_clearing(client):
    project = create(
        client, titulo=" " + "x" * 150 + " ", nome_subprojeto="s" * 150,
        edicao="e" * 30, equipe="t" * 50, data_prevista_execucao="2026-11-01",
    )
    assert project["titulo"] == "x" * 150
    response = client.patch(
        f"/projects/{project['id']}", json={"equipe": "", "data_prevista_execucao": None}
    )
    assert response.status_code == 200
    assert response.json()["equipe"] == "" and response.json()["data_prevista_execucao"] is None
    assert response.json()["nome_subprojeto"] == "s" * 150


@pytest.mark.parametrize("field,value", [
    ("id", 100), ("fase", "encerrado"), ("estoque", 1), ("executados", 1),
    ("criado_em", "2020-01-01T00:00:00Z"), ("atualizado_em", "2020-01-01T00:00:00Z"),
    ("data_entrada_fase", "2020-01-01T00:00:00Z"),
    ("descricao", "Antiga"), ("indice_satisfacao", 5), ("taxa_conversao", 50),
])
def test_read_only_and_removed_fields_rejected_on_post_and_patch(client, field, value):
    assert client.post("/projects", json=payload(**{field: value})).status_code == 422
    project = create(client)
    before = state(client, project["id"])
    assert client.patch(f"/projects/{project['id']}", json={field: value}).status_code == 422
    assert state(client, project["id"]) == before


def test_composite_duplicate_errors_identify_fields(client):
    first = create(client)
    duplicate = client.post("/projects", json=payload())
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["fields"] == [
        "codigo_projeto", "codigo_subprojeto", "edicao"
    ]
    second = create(client, codigo_subprojeto="04")
    assert second["id"] != first["id"]
    before = state(client, second["id"])
    conflict = client.patch(f"/projects/{second['id']}", json={"codigo_subprojeto": "03"})
    assert conflict.status_code == 409
    assert state(client, second["id"]) == before


def test_partial_patch_joint_validation_and_recalculation(client):
    project = create(client)
    project_id = project["id"]
    before = state(client, project_id)
    bad = client.patch(f"/projects/{project_id}", json={"selecionados": 7, "titulo": "Bad"})
    assert bad.status_code == 422 and bad.json()["detail"]["field"] == "avisados"
    assert state(client, project_id) == before
    accepted = client.patch(
        f"/projects/{project_id}", json={"selecionados": 9, "avisados": 9, "descartados": 9}
    )
    assert accepted.status_code == 200
    assert accepted.json()["estoque"] == accepted.json()["executados"] == 0
    assert accepted.json()["fase"] == "selecao"
    assert accepted.json()["titulo"] == project["titulo"]
    assert accepted.json()["criado_em"] == project["criado_em"]


def test_empty_null_and_unknown_project_errors(client):
    project = create(client)
    url = f"/projects/{project['id']}"
    assert client.patch(url, json={}).status_code == 422
    for field in ["titulo", "edicao", "selecionados", "avisados", "descartados", "data_inicio_fase"]:
        assert client.patch(url, json={field: None}).status_code == 422
    assert client.get("/projects/999").status_code == 404
    assert client.get("/projects/999/history").status_code == 404
    assert client.patch("/projects/999", json={"titulo": "X"}).status_code == 404
    assert client.delete("/projects/999").status_code == 404
    assert client.post("/projects/999/phase", json={"fase": "desenvolvimento"}).status_code == 404
    assert client.patch("/projects/999/history/1", json={"titulo": "X"}).status_code == 404


def test_workflow_dates_and_terminal_state(client):
    project = create(client)
    project_id = project["id"]
    url = f"/projects/{project_id}/phase"
    before = state(client, project_id)
    for invalid in ["selecao", "execucao", "encerrado"]:
        rejected = client.post(url, json={"fase": invalid})
        assert rejected.status_code == 409
        assert rejected.json()["detail"]["transicoes_permitidas"] == ["desenvolvimento"]
    for invalid_date in [None, "2026-10-04", "05/10/2026"]:
        assert client.post(url, json={
            "fase": "desenvolvimento", "data_inicio_fase": invalid_date
        }).status_code == 422
    assert state(client, project_id) == before
    for phase in ["desenvolvimento", "execucao", "pos_venda", "encerrado"]:
        response = client.post(url, json={"fase": phase, "data_inicio_fase": "2026-10-05"})
        assert response.status_code == 200, response.text
    final, history = state(client, project_id)
    assert final["fase"] == "encerrado" and final["transicoes_permitidas"] == []
    assert len(history) == 5
    assert client.post(url, json={"fase": "selecao"}).status_code == 409
    assert state(client, project_id) == (final, history)


def test_completed_phase_correction_and_neighbors(client):
    project = create(client, data_inicio_fase="2026-10-01")
    project_id = project["id"]
    assert client.post(f"/projects/{project_id}/phase", json={
        "fase": "desenvolvimento", "data_inicio_fase": "2026-10-05"
    }).status_code == 200
    assert client.post(f"/projects/{project_id}/phase", json={
        "fase": "execucao", "data_inicio_fase": "2026-10-07"
    }).status_code == 200
    current, history = state(client, project_id)
    target = history[1]
    url = f"/projects/{project_id}/history/{target['id']}"
    corrected = client.patch(url, json={
        "titulo": "Histórico corrigido", "data_inicio_fase": "2026-10-03", "descartados": 8
    })
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["executados"] == 0
    assert corrected.json()["alterado_em"] == target["alterado_em"]
    assert corrected.json()["fase_destino"] == target["fase_destino"]
    assert client.get(f"/projects/{project_id}").json() == current
    before = state(client, project_id)
    for day in ["2026-09-30", "2026-10-08"]:
        assert client.patch(url, json={"data_inicio_fase": day}).status_code == 422
        assert state(client, project_id) == before
    for field, value in [
        ("fase_destino", "encerrado"), ("fase_origem", "encerrado"), ("id", 999),
        ("projeto_id", 999), ("alterado_em", "2000-01-01T00:00:00Z"),
        ("criado_em", "2000-01-01T00:00:00Z"), ("estoque", 10), ("executados", 10),
    ]:
        assert client.patch(url, json={field: value}).status_code == 422
    assert state(client, project_id) == before
    assert client.patch(
        f"/projects/{project_id}/history/{history[-1]['id']}", json={"titulo": "X"}
    ).status_code == 422
    assert client.patch(f"/projects/{project_id}/history/9999", json={"titulo": "X"}).status_code == 404


def test_delete_returns_204_and_removes_project_and_history(client):
    project = create(client)
    project_id = project["id"]
    response = client.delete(f"/projects/{project_id}")
    assert response.status_code == 204 and response.content == b""
    assert client.get(f"/projects/{project_id}").status_code == 404
    assert client.get(f"/projects/{project_id}/history").status_code == 404
    assert client.get("/projects").json() == []
