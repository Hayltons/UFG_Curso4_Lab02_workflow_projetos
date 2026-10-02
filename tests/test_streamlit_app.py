from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from frontend.api_client import ApiError


PROJECT = {
    "id": 1, "titulo": "Projeto de teste", "descricao": "Descrição", "equipe": "Equipe A",
    "fase": "selecao", "data_entrada_fase": "2026-10-02T12:00:00Z",
    "criado_em": "2026-10-02T12:00:00Z", "atualizado_em": "2026-10-02T12:00:00Z",
    "alvos_planejados": 10, "clientes_sensibilizados": 2,
    "indice_satisfacao": None, "taxa_conversao": 20.0,
    "transicoes_permitidas": ["desenvolvimento"],
}


def app():
    return AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/streamlit_app.py", default_timeout=30)


def test_empty_list():
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[]):
        view = app().run()
        assert not view.exception
        assert "Nenhum projeto" in view.info[0].value


def test_api_unavailable():
    with patch("frontend.api_client.ApiClient.list_projects", side_effect=ApiError("API indisponível")):
        view = app().run()
        assert not view.exception
        assert view.error
        assert view.text[0].value == "API indisponível"


def test_create_only_on_submit_and_no_repeat_on_rerun():
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[]), patch(
        "frontend.api_client.ApiClient.create_project", return_value=PROJECT
    ) as create:
        view = app().run()
        view.sidebar.radio[0].set_value("Cadastrar").run()
        view.text_input[0].set_value("Novo projeto")
        view.text_input[1].set_value("Equipe B")
        view.run()
        create.assert_not_called()
        view.button[0].click().run()
        assert not view.exception
        create.assert_called_once()
        assert create.call_args.args[0]["titulo"] == "Novo projeto"
        view.run()
        create.assert_called_once()


def test_edit_does_not_send_phase_or_calculated_indicator():
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[PROJECT]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=deepcopy(PROJECT)
    ), patch("frontend.api_client.ApiClient.update_project", return_value=PROJECT) as update:
        view = app().run()
        view.radio(key="action").set_value("Editar").run()
        view.text_input[0].set_value("Título alterado")
        next(button for button in view.button if button.label == "Salvar alterações").click().run()
        assert not view.exception
        update.assert_called_once()
        payload = update.call_args.args[1]
        assert payload["titulo"] == "Título alterado"
        assert "fase" not in payload
        assert "taxa_conversao" not in payload
        view.run()
        update.assert_called_once()


def test_cancel_delete_does_not_write():
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[PROJECT]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=PROJECT
    ), patch("frontend.api_client.ApiClient.delete_project") as delete:
        view = app().run()
        view.radio(key="action").set_value("Excluir").run()
        assert next(button for button in view.button if button.label == "Excluir definitivamente").disabled
        view.checkbox[0].check().run()
        next(button for button in view.button if button.label == "Cancelar exclusão").click().run()
        assert not view.exception
        delete.assert_not_called()
        assert view.radio(key="action").value == "Detalhes e indicadores"


def test_delete_requires_confirmation_and_is_not_repeated():
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[PROJECT]) as listing, patch(
        "frontend.api_client.ApiClient.get_project", return_value=PROJECT
    ), patch("frontend.api_client.ApiClient.delete_project") as delete:
        view = app().run()
        view.radio(key="action").set_value("Excluir").run()
        delete.assert_not_called()
        view.checkbox[0].check().run()
        delete.side_effect = lambda project_id: setattr(listing, "return_value", [])
        next(button for button in view.button if button.label == "Excluir definitivamente").click().run()
        assert not view.exception
        delete.assert_called_once_with(1)
        view.run()
        delete.assert_called_once()


def test_phase_and_history_come_from_api():
    history = [{"fase_origem": "selecao", "fase_destino": "desenvolvimento", "alterado_em": "2026-10-02T12:00:00Z"}]
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[PROJECT]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=PROJECT
    ), patch("frontend.api_client.ApiClient.history", return_value=history), patch(
        "frontend.api_client.ApiClient.change_phase", return_value=PROJECT
    ) as change:
        view = app().run()
        view.radio(key="action").set_value("Workflow e histórico").run()
        assert not view.exception
        assert view.selectbox[1].options == ["Desenvolvimento"]
        assert len(view.dataframe) == 2
        next(button for button in view.button if button.label == "Confirmar mudança de fase").click().run()
        assert not view.exception
        change.assert_called_once_with(1, "desenvolvimento")
        view.run()
        change.assert_called_once()
