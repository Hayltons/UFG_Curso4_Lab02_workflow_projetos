import httpx
import pytest

from frontend.api_client import ApiClient, ApiError


def test_base_url_from_environment(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://example.test:8000/")
    assert ApiClient().base_url == "http://example.test:8000"


def test_list_uses_http_and_returns_data():
    def handler(request):
        assert request.method == "GET"
        assert str(request.url) == "http://api.test/projects"
        return httpx.Response(200, json=[{"id": 1, "equipe": "Equipe A"}])

    client = ApiClient("http://api.test", transport=httpx.MockTransport(handler))
    assert client.list_projects() == [{"id": 1, "equipe": "Equipe A"}]


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_write_timeout_is_not_retried(method):
    requests = []

    def handler(request):
        requests.append(request)
        raise httpx.ReadTimeout("timeout", request=request)

    client = ApiClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ApiError, match="operação pode ter sido concluída"):
        client.request(method, "/projects/1", {"titulo": "Projeto"})
    assert len(requests) == 1


def test_connection_error_is_user_readable():
    def handler(request):
        raise httpx.ConnectError("internal details", request=request)

    client = ApiClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ApiError, match="Não foi possível acessar a API"):
        client.list_projects()


@pytest.mark.parametrize("status", [404, 409, 422])
def test_http_rejection_preserves_status(status):
    client = ApiClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(status, json={"detail": "Operação rejeitada"})
    ))
    with pytest.raises(ApiError, match="Operação rejeitada") as error:
        client.get_project(1)
    assert error.value.status_code == status


def test_validation_error_identifies_field():
    client = ApiClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(422, json={"detail": [
            {"loc": ["body", "titulo"], "msg": "Campo obrigatório"}
        ]})
    ))
    with pytest.raises(ApiError, match="titulo: Campo obrigatório"):
        client.create_project({})


def test_server_error_does_not_expose_internal_details():
    client = ApiClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(500, json={"detail": "database password"})
    ))
    with pytest.raises(ApiError) as error:
        client.list_projects()
    assert "database password" not in str(error.value)


def test_invalid_json_is_reported():
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
