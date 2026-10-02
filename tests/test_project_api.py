from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.main as main_module
from app.database import Base, get_db


@pytest.fixture
def client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    engine = create_engine(f"sqlite:///{tmp_path / 'api-test.db'}")
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(main_module, "engine", engine)

    def override_get_db():
        with TestingSession() as session:
            yield session

    main_module.app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(main_module.app) as test_client:
            yield test_client
    finally:
        main_module.app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def payload(**overrides):
    body = {"titulo": "Projeto", "equipe": "Equipe A"}
    body.update(overrides)
    return body


def create(client, **overrides):
    response = client.post("/projects", json=payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_health_and_empty_list(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["timestamp"].endswith("Z")
    assert client.get("/projects").json() == []


def test_create_list_detail_and_initial_history(client):
    project = create(client, alvos_planejados=4, clientes_sensibilizados=1)
    assert project["fase"] == "selecao"
    assert project["taxa_conversao"] == 25
    assert project["transicoes_permitidas"] == ["desenvolvimento"]
    detail = client.get(f"/projects/{project['id']}")
    assert detail.status_code == 200
    assert detail.json()["data_entrada_fase"].endswith("Z")
    history = client.get(f"/projects/{project['id']}/history").json()
    assert len(history) == 1
    assert history[0]["fase_origem"] is None
    assert history[0]["fase_destino"] == "selecao"
    assert history[0]["alterado_em"].endswith("Z")


def test_create_rejects_invalid_satisfaction_and_negative_counts(client):
    assert client.post("/projects", json=payload(indice_satisfacao=10.1)).status_code == 422
    assert client.post("/projects", json=payload(indice_satisfacao=-0.1)).status_code == 422
    assert client.post("/projects", json=payload(alvos_planejados=-1)).status_code == 422
    assert client.post("/projects", json=payload(clientes_sensibilizados=-1)).status_code == 422


def test_conversion_zero_rounding_and_over_one_hundred_percent(client):
    no_targets = create(client, clientes_sensibilizados=4)
    assert no_targets["taxa_conversao"] is None
    rounded = create(client, titulo="Arredondamento", alvos_planejados=800, clientes_sensibilizados=1)
    assert rounded["taxa_conversao"] == 0.13
    above = create(client, titulo="Acima de cem", alvos_planejados=2, clientes_sensibilizados=5)
    assert above["taxa_conversao"] == 250


def test_transition_acceptance_and_skip_rejection(client):
    project = create(client)
    project_id = project["id"]
    rejected = client.post(f"/projects/{project_id}/phase", json={"fase": "execucao"})
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["transicoes_permitidas"] == ["desenvolvimento"]
    assert len(client.get(f"/projects/{project_id}/history").json()) == 1
    accepted = client.post(f"/projects/{project_id}/phase", json={"fase": "desenvolvimento"})
    assert accepted.status_code == 200
    assert accepted.json()["fase"] == "desenvolvimento"
    assert accepted.json()["transicoes_permitidas"] == ["execucao"]
    history = client.get(f"/projects/{project_id}/history").json()
    assert [(entry["fase_origem"], entry["fase_destino"]) for entry in history] == [
        (None, "selecao"), ("selecao", "desenvolvimento")
    ]


def test_phase_is_not_edited_with_project_fields(client):
    project = create(client)
    response = client.patch(f"/projects/{project['id']}", json={"fase": "encerrado"})
    assert response.status_code == 422
    assert client.get(f"/projects/{project['id']}").json()["fase"] == "selecao"


def test_update_recalculates_and_delete_removes_history(client):
    project = create(client, alvos_planejados=4, clientes_sensibilizados=1)
    project_id = project["id"]
    updated = client.patch(f"/projects/{project_id}", json={
        "alvos_planejados": 3, "clientes_sensibilizados": 2, "indice_satisfacao": 9.5
    })
    assert updated.status_code == 200
    assert updated.json()["taxa_conversao"] == 66.67
    assert updated.json()["indice_satisfacao"] == 9.5
    assert updated.json()["fase"] == "selecao"
    assert client.delete(f"/projects/{project_id}").status_code == 204
    assert client.get(f"/projects/{project_id}").status_code == 404
    assert client.get(f"/projects/{project_id}/history").status_code == 404
    assert client.get("/projects").json() == []


def test_unknown_project_and_empty_update(client):
    assert client.get("/projects/99").status_code == 404
    existing = create(client)
    assert client.patch(f"/projects/{existing['id']}", json={"titulo": None}).status_code == 422
    assert client.patch("/projects/99", json={"titulo": "Novo"}).status_code == 404
    assert client.delete("/projects/99").status_code == 404
    assert client.post("/projects/99/phase", json={"fase": "desenvolvimento"}).status_code == 404
    assert client.patch("/projects/1", json={}).status_code == 422


def test_encerrado_has_no_outgoing_transitions(client):
    project = create(client)
    project_id = project["id"]
    for phase in ["desenvolvimento", "execucao", "pos_venda", "encerrado"]:
        response = client.post(f"/projects/{project_id}/phase", json={"fase": phase})
        assert response.status_code == 200
    final = client.get(f"/projects/{project_id}").json()
    assert final["fase"] == "encerrado"
    assert final["transicoes_permitidas"] == []
    rejected = client.post(f"/projects/{project_id}/phase", json={"fase": "selecao"})
    assert rejected.status_code == 409
    assert len(client.get(f"/projects/{project_id}/history").json()) == 5
