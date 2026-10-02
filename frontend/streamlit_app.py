"""Interface Streamlit. Execute pela raiz: python -m streamlit run frontend/streamlit_app.py."""

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


def show_error(error: Exception) -> None:
    st.error("Não foi possível concluir a operação.")
    st.text(str(error))


def success(message: str) -> None:
    st.session_state["flash"] = message
    st.rerun()


def project_form(client: ApiClient, project: dict[str, Any] | None = None) -> None:
    values = project or {}
    form_key = f"project_{values.get('id', 'new')}_{values.get('atualizado_em', '')}"
    with st.form(form_key):
        title = st.text_input("Título", value=values.get("titulo", ""))
        description = st.text_area("Descrição", value=values.get("descricao", ""))
        team = st.text_input("Equipe responsável", value=values.get("equipe", ""))
        targets = st.number_input(
            "Alvos planejados", min_value=0, value=values.get("alvos_planejados", 0), step=1
        )
        customers = st.number_input(
            "Clientes sensibilizados", min_value=0,
            value=values.get("clientes_sensibilizados", 0), step=1
        )
        satisfaction = values.get("indice_satisfacao")
        satisfaction_text = st.text_input(
            "Índice de satisfação (opcional)",
            value="" if satisfaction is None else str(satisfaction),
            help="Deixe vazio quando ainda não houver avaliação.",
        )
        submitted = st.form_submit_button("Salvar alterações" if project else "Cadastrar projeto")
    if not submitted:
        return
    try:
        satisfaction_value = (
            float(satisfaction_text.replace(",", ".")) if satisfaction_text.strip() else None
        )
    except ValueError:
        st.error("Índice de satisfação: informe um número ou deixe vazio.")
        return
    payload = {
        "titulo": title,
        "descricao": description,
        "equipe": team,
        "alvos_planejados": targets,
        "clientes_sensibilizados": customers,
        "indice_satisfacao": satisfaction_value,
    }
    try:
        if project:
            client.update_project(project["id"], payload)
        else:
            client.create_project(payload)
            st.session_state["created"] = True
        success("Projeto atualizado." if project else "Projeto cadastrado.")
    except ApiError as exc:
        show_error(exc)


def details(project: dict[str, Any]) -> None:
    st.subheader("Dados do projeto")
    st.text(f"Título: {project['titulo']}")
    st.text(f"Descrição: {project.get('descricao', '')}")
    st.text(f"Equipe: {project['equipe']}")
    st.text(f"Fase atual: {PHASE_LABELS.get(project['fase'], project['fase'])}")
    st.text(f"Entrada na fase: {project['data_entrada_fase']}")
    st.text(f"Criado em: {project['criado_em']}")
    st.text(f"Atualizado em: {project['atualizado_em']}")
    st.subheader("Indicadores operacionais")
    st.text(f"Alvos planejados: {project['alvos_planejados']}")
    st.text(f"Clientes sensibilizados: {project['clientes_sensibilizados']}")
    satisfaction = project.get("indice_satisfacao")
    conversion = project.get("taxa_conversao")
    st.text(f"Satisfação: {satisfaction if satisfaction is not None else 'Não informada'}")
    st.text(f"Conversão: {str(conversion) + '%' if conversion is not None else 'Não disponível'}")


def workflow(client: ApiClient, project: dict[str, Any]) -> None:
    st.subheader("Workflow")
    st.text("Seleção → Desenvolvimento → Execução → Pós-venda → Encerrado")
    st.text(f"Fase atual: {PHASE_LABELS.get(project['fase'], project['fase'])}")
    # As opções vêm da API; a interface não replica a matriz de transições.
    allowed = project.get("transicoes_permitidas", [])
    if allowed:
        with st.form(f"phase_{project['id']}_{project['fase']}"):
            destination = st.selectbox(
                "Próxima fase", allowed, format_func=lambda value: PHASE_LABELS.get(value, value)
            )
            submitted = st.form_submit_button("Confirmar mudança de fase")
        if submitted:
            try:
                client.change_phase(project["id"], destination)
                success("Fase atualizada e histórico registrado.")
            except ApiError as exc:
                show_error(exc)
    else:
        st.info("Nenhuma mudança de fase disponível para este projeto.")

    st.subheader("Histórico de fases")
    try:
        records = client.history(project["id"])
    except ApiError as exc:
        show_error(exc)
        return
    if not records:
        st.info("Nenhum registro de fase disponível.")
        return
    st.dataframe([
        {
            "Origem": PHASE_LABELS.get(row.get("fase_origem"), "Entrada inicial"),
            "Destino": PHASE_LABELS.get(row["fase_destino"], row["fase_destino"]),
            "Data/hora": row["alterado_em"],
        }
        for row in records
    ], hide_index=True)


def delete_project(client: ApiClient, project: dict[str, Any]) -> None:
    st.subheader("Excluir projeto")
    st.text(f"Projeto #{project['id']}: {project['titulo']}")
    st.warning("A exclusão será enviada após sua confirmação.")
    confirmed = st.checkbox("Confirmo a exclusão deste projeto", key=f"delete_{project['id']}")
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
    st.set_page_config(page_title="Projetos em Workflow", layout="centered")
    st.title("Projetos em Workflow")
    if st.session_state.pop("created", False) or st.session_state.pop("deleted", False):
        st.session_state["navigation"] = "Projetos"
        st.session_state.pop("selected_project", None)
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
    st.dataframe([
        {"ID": item["id"], "Título": item["titulo"], "Equipe": item["equipe"],
         "Fase": PHASE_LABELS.get(item["fase"], item["fase"])}
        for item in projects
    ], hide_index=True)
    by_id = {item["id"]: item for item in projects}
    if st.session_state.get("selected_project") not in by_id:
        st.session_state["selected_project"] = next(iter(by_id))
    project_id = st.selectbox(
        "Selecionar projeto", list(by_id), key="selected_project",
        format_func=lambda value: f"#{value} — {by_id[value]['titulo']}",
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
