"""Streamlit Rev1 flows through mocked HTTP client calls."""

from copy import deepcopy
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from frontend.api_client import ApiError

TODAY = datetime.now(UTC).date()
AUDIT = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def project(**changes):
    values = {
        "id": 1, "codigo_projeto": "01.002", "codigo_subprojeto": "03",
        "titulo": "Projeto de teste", "nome_subprojeto": "Subprojeto",
        "edicao": "2026", "equipe": None, "data_prevista_execucao": None,
        "fase": "selecao", "data_inicio_fase": TODAY.isoformat(),
        "data_entrada_fase": AUDIT, "criado_em": AUDIT, "atualizado_em": AUDIT,
        "selecionados": 8, "avisados": 8, "descartados": 8,
        "estoque": 0, "executados": 0,
        "transicoes_permitidas": ["desenvolvimento"],
    }
    values.update(changes)
    return values


def history_record(source, event_id, destination, phase_date, origin=None):
    fields = [
        "codigo_projeto", "codigo_subprojeto", "titulo", "nome_subprojeto",
        "edicao", "equipe", "data_prevista_execucao", "selecionados", "avisados",
        "descartados", "estoque", "executados",
    ]
    return {
        "id": event_id, "projeto_id": source["id"], "fase_origem": origin,
        "fase_destino": destination, "data_inicio_fase": phase_date.isoformat(),
        "alterado_em": AUDIT, **{field: source[field] for field in fields},
    }


def app():
    return AppTest.from_file(
        Path(__file__).resolve().parents[1] / "frontend/streamlit_app.py",
        default_timeout=30,
    )


def button(view, label):
    return next(item for item in view.button if item.label == label)


def text_field(view, label):
    return next(item for item in view.text_input if item.label.startswith(label))


def date_field(view, label):
    return next(item for item in view.date_input if item.label.startswith(label))


def test_empty_list_and_unavailable_api():
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[]):
        view = app().run()
        assert not view.exception
        assert "Nenhum projeto" in view.info[0].value
    with patch(
        "frontend.api_client.ApiClient.list_projects",
        side_effect=ApiError("API indisponível"),
    ):
        view = app().run()
        assert not view.exception
        assert view.error and view.text[0].value == "API indisponível"


def test_listing_selection_with_same_project_code_and_all_fields():
    first = project()
    second = project(id=2, edicao="2027", titulo="Outra edição", codigo_subprojeto="04")
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[second, first]), patch(
        "frontend.api_client.ApiClient.get_project",
        side_effect=lambda project_id: deepcopy({1: first, 2: second}[project_id]),
    ) as get:
        view = app().run()
        assert not view.exception
        columns = set(view.dataframe[0].value.columns)
        for column in [
            "Código do projeto", "Código do subprojeto", "Nome do projeto",
            "Nome do subprojeto", "Edição", "Equipe", "Previsão de execução",
            "Fase", "Início da fase", "Selecionados (AP)", "Avisados (AS)",
            "Estoque", "Descartados (AD)", "Executados", "ID",
            "Entrada na fase (UTC)", "Criado em (UTC)", "Atualizado em (UTC)",
        ]:
            assert column in columns
        options = view.selectbox[0].options
        assert len(options) == 2
        assert all("01.002" in option for option in options)
        assert any("03 / 2026" in option for option in options)
        assert any("04 / 2027" in option for option in options)
        view.selectbox[0].set_value(2).run()
        assert not view.exception
        assert get.call_args.args == (2,)
        assert any("Executados: 0" in item.value for item in view.text)


def test_details_show_dates_zero_and_audit_as_read_only():
    record = project(
        data_inicio_fase="2026-10-05", data_prevista_execucao="2026-11-01",
        equipe="Equipe A",
    )
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[record]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=record,
    ):
        view = app().run()
        assert not view.exception
        text_values = [item.value for item in view.text]
        assert "Início da fase: 05/10/2026" in text_values
        assert "Previsão de execução: 01/11/2026" in text_values
        assert "Estoque: 0" in text_values
        assert "Executados: 0" in text_values
        assert f"Criado em (UTC): {AUDIT}" in text_values
        assert not view.number_input


def test_create_requires_submit_preserves_zeros_and_omits_derived():
    created = project()
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[]), patch(
        "frontend.api_client.ApiClient.create_project", return_value=created,
    ) as create:
        view = app().run()
        view.sidebar.radio[0].set_value("Cadastrar").run()
        assert not view.exception
        assert text_field(view, "Código do projeto").value == ""
        assert text_field(view, "Edição").value == ""
        for label in ["Código do projeto", "Código do subprojeto", "Nome do projeto", "Nome do subprojeto", "Edição", "Selecionados (AP)", "Avisados (AS)", "Descartados (AD)"]:
            assert text_field(view, label).label.endswith("*")
        assert not next(x for x in view.checkbox if x.label == "Informar previsão de execução").value
        for label, value in [
            ("Código do projeto", "01.002"), ("Código do subprojeto", "03"),
            ("Nome do projeto", "Novo projeto"), ("Nome do subprojeto", "Subprojeto"),
            ("Edição", "2026"), ("Selecionados (AP)", "8"),
            ("Avisados (AS)", "8"), ("Descartados (AD)", "8"),
        ]:
            text_field(view, label).set_value(value)
        view.run()
        create.assert_not_called()
        button(view, "Cadastrar projeto").click().run()
        assert not view.exception
        create.assert_called_once()
        payload = create.call_args.args[0]
        assert payload["codigo_projeto"] == "01.002"
        assert payload["codigo_subprojeto"] == "03"
        assert payload["equipe"] == ""
        assert payload["data_prevista_execucao"] is None
        assert payload["data_inicio_fase"] == TODAY
        assert (payload["selecionados"], payload["avisados"], payload["descartados"]) == (8, 8, 8)
        assert not {"estoque", "executados", "fase", "criado_em", "atualizado_em"} & payload.keys()
        view.run()
        create.assert_called_once()


def test_invalid_integer_and_api_422_keep_form_inputs():
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[]), patch(
        "frontend.api_client.ApiClient.create_project",
        side_effect=ApiError("titulo: Campo obrigatório", 422),
    ) as create:
        view = app().run()
        view.sidebar.radio[0].set_value("Cadastrar").run()
        text_field(view, "Selecionados (AP)").set_value("1.5")
        button(view, "Cadastrar projeto").click().run()
        assert not view.exception
        create.assert_not_called()
        assert "inteiro" in view.error[0].value
        text_field(view, "Selecionados (AP)").set_value("8")
        text_field(view, "Avisados (AS)").set_value("8")
        text_field(view, "Descartados (AD)").set_value("8")
        button(view, "Cadastrar projeto").click().run()
        assert not view.exception
        create.assert_called_once()
        assert "HTTP 422" in view.error[0].value
        assert text_field(view, "Selecionados (AP)").value == "8"
        assert text_field(view, "Código do projeto").value == ""


@pytest.mark.parametrize("status,message", [(409, "Chave duplicada"), (422, "Avisados inválidos")])
def test_edit_errors_keep_inputs_and_do_not_repeat_writes(status, message):
    record = project()
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[record]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=record,
    ), patch(
        "frontend.api_client.ApiClient.update_project",
        side_effect=ApiError(message, status),
    ) as update:
        view = app().run()
        view.radio(key="action").set_value("Editar").run()
        text_field(view, "Nome do projeto").set_value("Título corrigido")
        button(view, "Salvar alterações").click().run()
        assert not view.exception
        assert update.call_count == 1
        assert f"HTTP {status}" in view.error[0].value
        assert text_field(view, "Nome do projeto").value == "Título corrigido"
        view.run()
        assert update.call_count == 1


def test_edit_patch_optional_dates_and_read_only_derived():
    record = project(data_prevista_execucao="2026-11-01", equipe="Equipe A")
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[record]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=record,
    ), patch("frontend.api_client.ApiClient.update_project", return_value=record) as update:
        view = app().run()
        view.radio(key="action").set_value("Editar").run()
        assert any(item.value == "Executados: 0" for item in view.text)
        next(x for x in view.checkbox if x.label == "Informar previsão de execução").uncheck()
        text_field(view, "Nome do projeto").set_value("Corrigido")
        date_field(view, "Data de início da fase").set_value(TODAY - timedelta(days=1))
        button(view, "Salvar alterações").click().run()
        assert not view.exception
        update.assert_called_once()
        assert update.call_args.args[0] == 1
        payload = update.call_args.args[1]
        assert payload["data_prevista_execucao"] is None
        assert payload["data_inicio_fase"] == TODAY - timedelta(days=1)
        assert payload["titulo"] == "Corrigido"
        assert not {"fase", "estoque", "executados", "data_entrada_fase", "criado_em"} & payload.keys()
        view.run()
        update.assert_called_once()


def test_phase_date_suggestion_and_history_from_api():
    record = project(data_inicio_fase=(TODAY + timedelta(days=1)).isoformat())
    history = [history_record(record, 11, "selecao", TODAY)]
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[record]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=record,
    ), patch("frontend.api_client.ApiClient.history", return_value=history), patch(
        "frontend.api_client.ApiClient.change_phase", return_value=record,
    ) as change:
        view = app().run()
        view.radio(key="action").set_value("Workflow e histórico").run()
        assert not view.exception
        assert view.selectbox[1].options == ["Desenvolvimento"]
        proposed_date = date_field(view, "Data de início da nova fase").value
        assert proposed_date >= TODAY
        assert proposed_date >= date.fromisoformat(record["data_inicio_fase"])
        assert len(view.dataframe) == 2
        chosen_date = proposed_date + timedelta(days=2)
        date_field(view, "Data de início da nova fase").set_value(chosen_date)
        button(view, "Confirmar mudança de fase").click().run()
        assert not view.exception
        change.assert_called_once_with(1, "desenvolvimento", chosen_date)
        view.run()
        change.assert_called_once()


def test_completed_phase_correction_keeps_identity_and_audit_read_only():
    current = project(
        fase="execucao", data_inicio_fase=(TODAY + timedelta(days=2)).isoformat(),
        transicoes_permitidas=["pos_venda"],
    )
    events = [
        history_record(current, 11, "selecao", TODAY - timedelta(days=2)),
        history_record(current, 12, "desenvolvimento", TODAY, "selecao"),
        history_record(current, 13, "execucao", TODAY + timedelta(days=2), "desenvolvimento"),
    ]
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[current]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=current,
    ), patch("frontend.api_client.ApiClient.history", return_value=events), patch(
        "frontend.api_client.ApiClient.update_completed_phase", return_value=events[0],
    ) as update:
        view = app().run()
        view.radio(key="action").set_value("Workflow e histórico").run()
        assert not view.exception
        assert len(view.dataframe) == 2
        assert any("Horário UTC de auditoria" in item.value for item in view.caption)
        date_field(view, "Data de início da fase").set_value(TODAY - timedelta(days=1))
        text_field(view, "Nome do projeto").set_value("Nome anterior corrigido")
        button(view, "Salvar correção da fase concluída").click().run()
        assert not view.exception
        update.assert_called_once()
        project_id, event_id, payload = update.call_args.args
        assert (project_id, event_id) == (1, 11)
        assert payload["data_inicio_fase"] == TODAY - timedelta(days=1)
        assert payload["titulo"] == "Nome anterior corrigido"
        assert payload["avisados"] == payload["descartados"] == 8
        assert not {
            "fase", "fase_origem", "fase_destino", "id", "projeto_id",
            "alterado_em", "data_entrada_fase", "estoque", "executados",
        } & payload.keys()
        view.run()
        update.assert_called_once()


def test_terminal_phase_and_empty_history_need_no_writes():
    record = project(fase="encerrado", transicoes_permitidas=[])
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[record]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=record,
    ), patch("frontend.api_client.ApiClient.history", return_value=[]), patch(
        "frontend.api_client.ApiClient.change_phase",
    ) as change:
        view = app().run()
        view.radio(key="action").set_value("Workflow e histórico").run()
        assert not view.exception
        assert any("Encerrado" in item.value for item in view.info)
        assert any("Nenhum registro" in item.value for item in view.info)
        change.assert_not_called()


def test_cancel_delete_does_not_write():
    record = project()
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[record]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=record,
    ), patch("frontend.api_client.ApiClient.delete_project") as delete:
        view = app().run()
        view.radio(key="action").set_value("Excluir").run()
        assert "01.002 / 03 / 2026" in view.text[-1].value
        assert button(view, "Excluir definitivamente").disabled
        view.checkbox[0].check().run()
        button(view, "Cancelar exclusão").click().run()
        assert not view.exception
        delete.assert_not_called()
        assert view.radio(key="action").value == "Detalhes e indicadores"


def test_delete_requires_confirmation_and_is_not_repeated():
    record = project()
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[record]) as listing, patch(
        "frontend.api_client.ApiClient.get_project", return_value=record,
    ), patch("frontend.api_client.ApiClient.delete_project") as delete:
        view = app().run()
        view.radio(key="action").set_value("Excluir").run()
        delete.assert_not_called()
        view.checkbox[0].check().run()
        delete.side_effect = lambda project_id: setattr(listing, "return_value", [])
        button(view, "Excluir definitivamente").click().run()
        assert not view.exception
        delete.assert_called_once_with(1)
        view.run()
        delete.assert_called_once()


def test_get_project_404_shows_status_and_detail():
    record = project()
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[record]), patch(
        "frontend.api_client.ApiClient.get_project",
        side_effect=ApiError("Projeto não encontrado", 404),
    ):
        view = app().run()
        assert not view.exception
        assert "HTTP 404" in view.error[0].value
        assert view.text[0].value == "Projeto não encontrado"


def test_edit_timeout_does_not_repeat_write_on_rerun():
    record = project()
    with patch("frontend.api_client.ApiClient.list_projects", return_value=[record]), patch(
        "frontend.api_client.ApiClient.get_project", return_value=record,
    ), patch(
        "frontend.api_client.ApiClient.update_project",
        side_effect=ApiError("A operação pode ter sido concluída; confira a listagem.", None),
    ) as update:
        view = app().run()
        view.radio(key="action").set_value("Editar").run()
        text_field(view, "Nome do projeto").set_value("Correção")
        button(view, "Salvar alterações").click().run()
        assert not view.exception
        assert update.call_count == 1
        assert any("pode ter sido concluída" in item.value for item in view.text)
        view.run()
        assert update.call_count == 1
