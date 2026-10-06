"""HTTPX client contracts exercised without network access."""

from datetime import date

import httpx
import pytest

from frontend.api_client import ApiClient, ApiError


def test_base_url_from_environment(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://example.test:8000/")
    assert ApiClient().base_url == "http://example.test:8000"


def test_list_and_detail_keep_rev1_fields():
    project = {
        "id": 1, "codigo_projeto": "01.002", "codigo_subprojeto": "03",
        "edicao": "2026", "equipe": None, "data_prevista_execucao": None,
        "selecionados": 8, "avisados": 8, "descartados": 8,
        "estoque": 0, "executados": 0,
    }
    requests = []

    def handler(request):
        requests.append((request.method, request.url.path))
        return httpx.Response(200, json=[project] if request.url.path == "/projects" else project)

    client = ApiClient("http://api.test", transport=httpx.MockTransport(handler))
    assert client.list_projects() == [project]
    assert client.get_project(1) == project
    assert requests == [("GET", "/projects"), ("GET", "/projects/1")]


def test_create_and_patch_send_only_given_fields_with_iso_dates():
    requests = []

    def handler(request):
        requests.append((request.method, request.url.path, request.read()))
        return httpx.Response(201 if request.method == "POST" else 200, json={"id": 7})

    client = ApiClient("http://api.test", transport=httpx.MockTransport(handler))
    payload = {
        "codigo_projeto": "01.002", "codigo_subprojeto": "03",
        "titulo": "Projeto", "nome_subprojeto": "Subprojeto", "edicao": "2026",
        "equipe": None, "data_prevista_execucao": None,
        "data_inicio_fase": date(2026, 10, 5),
        "selecionados": 8, "avisados": 8, "descartados": 8,
    }
    assert client.create_project(payload) == {"id": 7}
    assert client.update_project(7, {"data_prevista_execucao": date(2026, 11, 1)}) == {"id": 7}
    assert [(method, path) for method, path, _ in requests] == [
        ("POST", "/projects"), ("PATCH", "/projects/7")
    ]
    import json
    posted = json.loads(requests[0][2])
    updated = json.loads(requests[1][2])
    assert posted["data_inicio_fase"] == "2026-10-05"
    assert posted["data_prevista_execucao"] is None
    assert posted["codigo_projeto"] == "01.002"
    assert posted["avisados"] == posted["descartados"] == 8
    assert not {"estoque", "executados", "fase", "criado_em"} & posted.keys()
    assert updated == {"data_prevista_execucao": "2026-11-01"}
    assert payload["data_inicio_fase"] == date(2026, 10, 5)


def test_phase_history_and_completed_phase_patch_use_api_contract():
    import json
    requests = []

    def handler(request):
        body = json.loads(request.read()) if request.method != "GET" else None
        requests.append((request.method, request.url.path, body))
        if request.method == "GET":
            return httpx.Response(200, json=[{"id": 11, "executados": 0}])
        return httpx.Response(200, json={"fase": "desenvolvimento"})

    client = ApiClient("http://api.test", transport=httpx.MockTransport(handler))
    assert client.change_phase(7, "desenvolvimento", date(2026, 10, 5))["fase"] == "desenvolvimento"
    assert client.history(7) == [{"id": 11, "executados": 0}]
    assert client.update_completed_phase(
        7, 11, {"data_inicio_fase": date(2026, 10, 4), "titulo": "Corrigido"}
    )["fase"] == "desenvolvimento"
    assert requests == [
        ("POST", "/projects/7/phase", {
            "fase": "desenvolvimento", "data_inicio_fase": "2026-10-05"
        }),
        ("GET", "/projects/7/history", None),
        ("PATCH", "/projects/7/history/11", {
            "data_inicio_fase": "2026-10-04", "titulo": "Corrigido"
        }),
    ]


def test_phase_date_is_omitted_when_not_given():
    import json
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.read()))
        return httpx.Response(200, json={"fase": "desenvolvimento"})

    ApiClient(transport=httpx.MockTransport(handler)).change_phase(1, "desenvolvimento")
    assert bodies == [{"fase": "desenvolvimento"}]


@pytest.mark.parametrize("method", ["POST", "PATCH", "DELETE"])
def test_write_timeout_is_not_retried(method):
    requests = []

    def handler(request):
        requests.append(request)
        raise httpx.ReadTimeout("internal timeout details", request=request)

    client = ApiClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ApiError, match="operação pode ter sido concluída") as error:
        client.request(method, "/projects/1", {"titulo": "Projeto"})
    assert error.value.status_code is None
    assert len(requests) == 1
    assert "internal timeout details" not in str(error.value)


def test_connection_error_is_user_readable():
    def handler(request):
        raise httpx.ConnectError("internal details", request=request)

    client = ApiClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ApiError, match="Não foi possível acessar a API"):
        client.list_projects()


@pytest.mark.parametrize("status,detail,expected", [
    (404, "Projeto 7 não encontrado.", "Projeto 7 não encontrado."),
    (409, {"fields": ["codigo_projeto", "codigo_subprojeto", "edicao"],
           "message": "Já existe."}, "codigo_projeto, codigo_subprojeto, edicao: Já existe."),
    (409, {"message": "A fase não é permitida.",
           "transicoes_permitidas": ["desenvolvimento"]}, "A fase não é permitida."),
    (422, {"field": "avisados", "message": "Avisados supera Selecionados."},
     "avisados: Avisados supera Selecionados."),
    (422, [{"loc": ["body", "data_prevista_execucao"], "msg": "Data inválida."}],
     "data_prevista_execucao: Data inválida."),
])
def test_api_errors_keep_status_and_explain_field(status, detail, expected):
    client = ApiClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(status, json={"detail": detail})
    ))
    with pytest.raises(ApiError) as error:
        client.get_project(7)
    assert error.value.status_code == status
    assert str(error.value) == expected


def test_fallbacks_do_not_expose_internal_server_details():
    for status, body in [
        (404, "not json"), (409, "{}"), (422, '{"detail": null}'),
        (500, '{"detail": "database password"}'),
    ]:
        client = ApiClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(status, text=body)
        ))
        with pytest.raises(ApiError) as error:
            client.list_projects()
        assert error.value.status_code == status
        assert "database password" not in str(error.value)
        assert str(error.value)


def test_invalid_success_json_is_reported():
    client = ApiClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, text="invalid JSON")
    ))
    with pytest.raises(ApiError, match="resposta inválida"):
        client.list_projects()


def test_delete_accepts_empty_response():
    requests = []

    def handler(request):
        requests.append((request.method, request.url.path))
        return httpx.Response(204)

    client = ApiClient(transport=httpx.MockTransport(handler))
    assert client.delete_project(7) is None
    assert requests == [("DELETE", "/projects/7")]
