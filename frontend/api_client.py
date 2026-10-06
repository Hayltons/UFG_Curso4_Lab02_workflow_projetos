"""Cliente HTTP da interface; não depende das camadas internas do back-end."""

import os
from datetime import date, datetime
from typing import Any

import httpx


class ApiError(Exception):
    """Falha de comunicação ou rejeição de uma operação pela API."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    @staticmethod
    def _json_value(value: Any) -> Any:
        """Serialize dates from UI widgets without changing business values."""
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: ApiClient._json_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [ApiClient._json_value(item) for item in value]
        return value

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
        ).rstrip("/")
        self.timeout = timeout
        self.transport = transport

    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> Any:
        try:
            with httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = client.request(
                    method, path,
                    json=self._json_value(payload) if payload is not None else None,
                )
        except httpx.TimeoutException as exc:
            message = "A API demorou para responder."
            if method not in {"GET", "HEAD"}:
                message += " Consulte os dados antes de tentar novamente: a operação pode ter sido concluída."
            raise ApiError(message) from exc
        except httpx.RequestError as exc:
            raise ApiError("Não foi possível acessar a API. Verifique se ela está disponível.") from exc

        if not response.is_success:
            raise ApiError(self._error_message(response), response.status_code)
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise ApiError("A API retornou uma resposta inválida.") from exc

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        if response.status_code >= 500:
            return "A API não conseguiu concluir a operação. Tente consultar os dados novamente."
        defaults = {
            404: "Projeto não encontrado. Atualize a listagem.",
            409: "A operação conflita com o estado atual do projeto. Atualize os dados.",
            422: "Verifique os campos informados.",
        }
        fallback = defaults.get(response.status_code, "A API rejeitou a operação.")
        try:
            body = response.json()
        except ValueError:
            return fallback
        detail = body.get("detail") if isinstance(body, dict) else None
        if isinstance(detail, str):
            return detail
        if isinstance(detail, dict):
            message = detail.get("message")
            if isinstance(message, str) and message:
                field = detail.get("field")
                if isinstance(field, str) and field:
                    return f"{field}: {message}"
                fields = detail.get("fields")
                if isinstance(fields, list) and fields and all(
                    isinstance(item, str) for item in fields
                ):
                    return f"{', '.join(fields)}: {message}"
                return message
        if isinstance(detail, list):
            errors = []
            for error in detail:
                if isinstance(error, dict):
                    location = error.get("loc", [])
                    field = ".".join(str(part) for part in location if part != "body")
                    message = error.get("msg", "Valor inválido")
                    if not isinstance(message, str):
                        message = "Valor inválido"
                    errors.append(f"{field}: {message}" if field else message)
            if errors:
                return "\n".join(errors)
        return fallback

    def list_projects(self) -> list[dict[str, Any]]:
        return self.request("GET", "/projects")

    def get_project(self, project_id: int) -> dict[str, Any]:
        return self.request("GET", f"/projects/{project_id}")

    def create_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/projects", payload)

    def update_project(self, project_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", f"/projects/{project_id}", payload)

    def delete_project(self, project_id: int) -> None:
        self.request("DELETE", f"/projects/{project_id}")

    def change_phase(
        self, project_id: int, phase: str, data_inicio_fase: date | str | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"fase": phase}
        if data_inicio_fase is not None:
            payload["data_inicio_fase"] = data_inicio_fase
        return self.request("POST", f"/projects/{project_id}/phase", payload)

    def history(self, project_id: int) -> list[dict[str, Any]]:
        return self.request("GET", f"/projects/{project_id}/history")

    def update_completed_phase(
        self, project_id: int, event_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self.request("PATCH", f"/projects/{project_id}/history/{event_id}", payload)
