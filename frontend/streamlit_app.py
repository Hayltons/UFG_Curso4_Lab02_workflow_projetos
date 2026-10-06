"""Interface Streamlit da Rev1; execute pela raiz do repositório."""

from datetime import UTC, date, datetime
from typing import Any

import streamlit as st

from frontend.api_client import ApiClient, ApiError


PHASE_LABELS = {
    "selecao": "Seleção",
    "desenvolvimento": "Desenvolvimento",
    "execucao": "Execução",
    "pos_venda": "Pós-venda",
    "encerrado": "Encerrado",
}


def _today_utc() -> date:
    return datetime.now(UTC).date()


def _as_date(value: date | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _display_date(value: date | str | None) -> str:
    if value is None:
        return "Não informada"
    try:
        parsed = _as_date(value)
    except ValueError:
        return str(value)
    return parsed.strftime("%d/%m/%Y") if parsed else "Não informada"


def _display_value(value: Any) -> Any:
    return "Não informada" if value is None or value == "" else value


def _phase_label(value: str | None) -> str:
    return "Entrada inicial" if value is None else PHASE_LABELS.get(value, value)


def _project_label(project: dict[str, Any]) -> str:
    return (
        f"{project['codigo_projeto']} / {project['codigo_subprojeto']} / "
        f"{project['edicao']} — {project['titulo']}"
    )


def show_error(error: ApiError) -> None:
    suffix = f" (HTTP {error.status_code})" if error.status_code is not None else ""
    st.error(f"Não foi possível concluir a operação{suffix}.")
    st.text(str(error))


def success(message: str) -> None:
    st.session_state["flash"] = message
    st.rerun()


def _business_fields(
    values: dict[str, Any], *, min_phase_date: date | None = None,
    max_phase_date: date | None = None,
) -> dict[str, Any]:
    """Collect only writable business fields; the API remains authoritative."""
    codigo_projeto = st.text_input(
        "Código do projeto (NN.NNN) *", value=values.get("codigo_projeto") or ""
    )
    codigo_subprojeto = st.text_input(
        "Código do subprojeto (NN) *", value=values.get("codigo_subprojeto") or ""
    )
    titulo = st.text_input("Nome do projeto *", value=values.get("titulo") or "")
    nome_subprojeto = st.text_input(
        "Nome do subprojeto *", value=values.get("nome_subprojeto") or ""
    )
    edicao = st.text_input("Edição *", value=values.get("edicao") or "")
    equipe = st.text_input("Equipe responsável (opcional)", value=values.get("equipe") or "")

    forecast = _as_date(values.get("data_prevista_execucao"))
    has_forecast = st.checkbox(
        "Informar previsão de execução", value=forecast is not None
    )
    forecast_date = st.date_input(
        "Data prevista para execução (DD/MM/AAAA)",
        value=forecast or _today_utc(),
        format="DD/MM/YYYY",
        disabled=not has_forecast,
    )
    current_phase_date = _as_date(values.get("data_inicio_fase")) or _today_utc()
    phase_date = st.date_input(
        "Data de início da fase (DD/MM/AAAA) *",
        value=current_phase_date,
        min_value=min_phase_date,
        max_value=max_phase_date,
        format="DD/MM/YYYY",
    )

    selecionados = st.text_input(
        "Selecionados (AP) *", value=str(values.get("selecionados") or "")
    )
    avisados = st.text_input(
        "Avisados (AS) *", value=str(values.get("avisados") or "")
    )
    descartados = st.text_input(
        "Descartados (AD) *", value=str(values.get("descartados") or "")
    )
    return {
        "codigo_projeto": codigo_projeto,
        "codigo_subprojeto": codigo_subprojeto,
        "titulo": titulo,
        "nome_subprojeto": nome_subprojeto,
        "edicao": edicao,
        "equipe": equipe,
        "data_prevista_execucao": forecast_date if has_forecast else None,
        "data_inicio_fase": phase_date,
        "selecionados": selecionados,
        "avisados": avisados,
        "descartados": descartados,
    }


def _integer_inputs(fields: dict[str, Any]) -> dict[str, Any] | None:
    """Parse widget text to JSON integers; business limits stay in the API."""
    payload = fields.copy()
    labels = {
        "selecionados": "Selecionados (AP)",
        "avisados": "Avisados (AS)",
        "descartados": "Descartados (AD)",
    }
    for name, label in labels.items():
        try:
            payload[name] = int(payload[name].strip())
        except ValueError:
            st.error(f"{label}: informe um número inteiro.")
            return None
    return payload


def _derived_read_only(values: dict[str, Any]) -> None:
    st.caption("Estoque e Executados são calculados pela API e não são editáveis.")
    if "estoque" in values:
        st.text(f"Estoque: {_display_value(values['estoque'])}")
    if "executados" in values:
        st.text(f"Executados: {_display_value(values['executados'])}")


def project_form(client: ApiClient, project: dict[str, Any] | None = None) -> None:
    values = project or {}
    form_key = f"project_{values.get('id', 'new')}_{values.get('atualizado_em', '')}"
    _derived_read_only(values)
    with st.form(form_key):
        fields = _business_fields(values)
        submitted = st.form_submit_button("Salvar alterações" if project else "Cadastrar projeto")
    if not submitted:
        return
    payload = _integer_inputs(fields)
    if payload is None:
        return
    try:
        if project:
            client.update_project(project["id"], payload)
            success("Projeto atualizado.")
        else:
            created = client.create_project(payload)
            st.session_state["created_project_id"] = created["id"]
            success("Projeto cadastrado.")
    except ApiError as exc:
        show_error(exc)


def _project_row(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "Código do projeto": project["codigo_projeto"],
        "Código do subprojeto": project["codigo_subprojeto"],
        "Nome do projeto": project["titulo"],
        "Nome do subprojeto": project["nome_subprojeto"],
        "Edição": project["edicao"],
        "Equipe": _display_value(project.get("equipe")),
        "Previsão de execução": _display_date(project.get("data_prevista_execucao")),
        "Fase": _phase_label(project["fase"]),
        "Início da fase": _display_date(project["data_inicio_fase"]),
        "Selecionados (AP)": project["selecionados"],
        "Avisados (AS)": project["avisados"],
        "Estoque": project["estoque"],
        "Descartados (AD)": project["descartados"],
        "Executados": project["executados"],
        "ID": project["id"],
        "Entrada na fase (UTC)": project["data_entrada_fase"],
        "Criado em (UTC)": project["criado_em"],
        "Atualizado em (UTC)": project["atualizado_em"],
    }


def details(project: dict[str, Any]) -> None:
    st.subheader("Dados do projeto")
    st.text(f"Código do projeto: {project['codigo_projeto']}")
    st.text(f"Código do subprojeto: {project['codigo_subprojeto']}")
    st.text(f"Nome do projeto: {project['titulo']}")
    st.text(f"Nome do subprojeto: {project['nome_subprojeto']}")
    st.text(f"Edição: {project['edicao']}")
    st.text(f"Equipe: {_display_value(project.get('equipe'))}")
    st.text(f"Previsão de execução: {_display_date(project.get('data_prevista_execucao'))}")
    st.text(f"Fase atual: {_phase_label(project['fase'])}")
    st.text(f"Início da fase: {_display_date(project['data_inicio_fase'])}")
    st.subheader("Indicadores operacionais")
    st.text(f"Selecionados (AP): {project['selecionados']}")
    st.text(f"Avisados (AS): {project['avisados']}")
    st.text(f"Estoque: {project['estoque']}")
    st.text(f"Descartados (AD): {project['descartados']}")
    st.text(f"Executados: {project['executados']}")
    st.caption("Estoque e Executados são calculados pela API.")
    st.subheader("Auditoria UTC")
    st.text(f"ID técnico: {project['id']}")
    st.text(f"Entrada na fase (UTC): {project['data_entrada_fase']}")
    st.text(f"Criado em (UTC): {project['criado_em']}")
    st.text(f"Atualizado em (UTC): {project['atualizado_em']}")


def _history_row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "Origem": _phase_label(record.get("fase_origem")),
        "Destino": _phase_label(record["fase_destino"]),
        "Início da fase": _display_date(record["data_inicio_fase"]),
        "Código do projeto": _display_value(record.get("codigo_projeto")),
        "Código do subprojeto": _display_value(record.get("codigo_subprojeto")),
        "Nome do projeto": _display_value(record.get("titulo")),
        "Nome do subprojeto": _display_value(record.get("nome_subprojeto")),
        "Edição": _display_value(record.get("edicao")),
        "Equipe": _display_value(record.get("equipe")),
        "Previsão": _display_date(record.get("data_prevista_execucao")),
        "Selecionados (AP)": _display_value(record.get("selecionados")),
        "Avisados (AS)": _display_value(record.get("avisados")),
        "Estoque": _display_value(record.get("estoque")),
        "Descartados (AD)": _display_value(record.get("descartados")),
        "Executados": _display_value(record.get("executados")),
        "Evento ID": record["id"],
        "Alterado em (UTC)": record["alterado_em"],
    }


def _edit_completed_phase(
    client: ApiClient, project_id: int, records: list[dict[str, Any]]
) -> None:
    completed = records[:-1]
    if not completed:
        st.info("Ainda não há fase concluída para corrigir.")
        return
    by_id = {record["id"]: (index, record) for index, record in enumerate(records)}
    selected_id = st.selectbox(
        "Fase concluída para corrigir",
        [record["id"] for record in completed],
        format_func=lambda event_id: (
            f"{_phase_label(by_id[event_id][1]['fase_destino'])} — "
            f"{_display_date(by_id[event_id][1]['data_inicio_fase'])} — "
            f"evento #{event_id}"
        ),
    )
    index, record = by_id[selected_id]
    previous_date = _as_date(records[index - 1]["data_inicio_fase"]) if index else None
    next_date = _as_date(records[index + 1]["data_inicio_fase"])
    st.caption(
        "Data permitida entre "
        f"{_display_date(previous_date) if previous_date else 'o início do projeto'} "
        f"e {_display_date(next_date)}. Horário UTC de auditoria: "
        f"{record['alterado_em']} (somente leitura)."
    )
    _derived_read_only(record)
    with st.form(f"history_{project_id}_{selected_id}_{record['alterado_em']}"):
        fields = _business_fields(
            record, min_phase_date=previous_date, max_phase_date=next_date
        )
        submitted = st.form_submit_button("Salvar correção da fase concluída")
    if not submitted:
        return
    payload = _integer_inputs(fields)
    if payload is None:
        return
    try:
        client.update_completed_phase(project_id, selected_id, payload)
        success("Fase concluída corrigida.")
    except ApiError as exc:
        show_error(exc)


def workflow(client: ApiClient, project: dict[str, Any]) -> None:
    st.subheader("Workflow")
    st.text("Seleção → Desenvolvimento → Execução → Pós-venda → Encerrado")
    st.text(f"Fase atual: {_phase_label(project['fase'])}")
    allowed = project.get("transicoes_permitidas", [])
    if allowed:
        suggested = max(_today_utc(), _as_date(project["data_inicio_fase"]))
        with st.form(f"phase_{project['id']}_{project['fase']}"):
            destination = st.selectbox(
                "Próxima fase", allowed, format_func=_phase_label
            )
            phase_date = st.date_input(
                "Data de início da nova fase (DD/MM/AAAA)",
                value=suggested,
                min_value=suggested,
                format="DD/MM/YYYY",
            )
            submitted = st.form_submit_button("Confirmar mudança de fase")
        if submitted:
            try:
                client.change_phase(project["id"], destination, phase_date)
                success("Fase atualizada e histórico registrado.")
            except ApiError as exc:
                show_error(exc)
    else:
        st.info("Nenhuma mudança de fase disponível: projeto Encerrado.")

    st.subheader("Histórico de fases")
    try:
        records = client.history(project["id"])
    except ApiError as exc:
        show_error(exc)
        return
    if not records:
        st.info("Nenhum registro de fase disponível.")
        return
    st.dataframe([_history_row(row) for row in records], hide_index=True)
    st.subheader("Corrigir fase concluída")
    _edit_completed_phase(client, project["id"], records)


def delete_project(client: ApiClient, project: dict[str, Any]) -> None:
    st.subheader("Excluir projeto")
    st.text(f"{_project_label(project)} (ID #{project['id']})")
    st.warning("A exclusão remove o projeto e seu histórico após confirmação.")
    confirmed = st.checkbox(
        "Confirmo a exclusão deste projeto", key=f"delete_{project['id']}"
    )
    if st.button("Cancelar exclusão"):
        st.session_state["cancel_delete"] = project["id"]
        st.rerun()
    if st.button("Excluir definitivamente", disabled=not confirmed):
        try:
            client.delete_project(project["id"])
            st.session_state["deleted"] = True
            success("Projeto excluído.")
        except ApiError as exc:
            show_error(exc)


def main() -> None:
    st.set_page_config(page_title="Projetos em Workflow", layout="wide")
    st.title("Projetos em Workflow")
    if st.session_state.pop("deleted", False):
        st.session_state["navigation"] = "Projetos"
        st.session_state.pop("selected_project", None)
    created_id = st.session_state.pop("created_project_id", None)
    if created_id is not None:
        st.session_state["navigation"] = "Projetos"
        st.session_state["selected_project"] = created_id
    cancelled_id = st.session_state.pop("cancel_delete", None)
    if cancelled_id is not None:
        st.session_state.pop(f"delete_{cancelled_id}", None)
        st.session_state["action"] = "Detalhes e indicadores"
    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)

    page = st.sidebar.radio("Navegação", ["Projetos", "Cadastrar"], key="navigation")
    client = ApiClient()
    if page == "Cadastrar":
        st.subheader("Cadastrar projeto")
        project_form(client)
        return

    st.subheader("Projetos cadastrados")
    st.button("Atualizar listagem")
    try:
        projects = client.list_projects()
    except ApiError as exc:
        show_error(exc)
        return
    if not projects:
        st.info("Nenhum projeto cadastrado. Use Cadastrar para começar.")
        return

    projects = sorted(
        projects,
        key=lambda item: (
            item["codigo_projeto"], item["codigo_subprojeto"],
            item["edicao"], item["id"],
        ),
    )
    st.dataframe([_project_row(item) for item in projects], hide_index=True)
    by_id = {item["id"]: item for item in projects}
    if st.session_state.get("selected_project") not in by_id:
        st.session_state["selected_project"] = next(iter(by_id))
    project_id = st.selectbox(
        "Selecionar projeto pelo código, subprojeto e edição",
        list(by_id),
        key="selected_project",
        format_func=lambda value: _project_label(by_id[value]),
    )
    try:
        project = client.get_project(project_id)
    except ApiError as exc:
        show_error(exc)
        return
    action = st.radio(
        "Ação", ["Detalhes e indicadores", "Editar", "Workflow e histórico", "Excluir"],
        key="action",
    )
    if action == "Detalhes e indicadores":
        details(project)
    elif action == "Editar":
        project_form(client, project)
    elif action == "Workflow e histórico":
        workflow(client, project)
    else:
        delete_project(client, project)


if __name__ == "__main__":
    main()
