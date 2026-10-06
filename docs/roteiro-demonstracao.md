# Roteiro de demonstração — MVP Rev1

**Duração alvo:** até 5 minutos, com API e Streamlit já iniciados. **Estado:** roteiro preparado no CAP06-P03 e checklist aceito. Por escolha do usuário, a apresentação será feita após a publicação dos prompts CAP07.

## Preparação autorizada antes da apresentação

Use um banco de demonstração SQLite **separado** do `projects.db` operacional, por exemplo `sqlite:///./demo_entrega.db`, somente após conferir que o caminho está ausente ou identificar seu conteúdo e autorizar seu uso. Inicie a API na raiz com essa `DATABASE_URL` e a interface com `API_BASE_URL=http://127.0.0.1:8000`, conforme o [README](../README.md). Não apague o banco operacional nem limpe o banco de demonstração automaticamente. A criação e exclusão de dados de demonstração abaixo são ações para o apresentador executar com autorização própria; este documento não as executa.

Anote o **dia UTC da apresentação**. Use a data do dia anterior como início de Seleção e o dia UTC atual para Desenvolvimento. Na tela, informe datas em DD/MM/AAAA; na API, em YYYY-MM-DD. Prepare o navegador em `http://127.0.0.1:8501` e a documentação da API em `http://127.0.0.1:8000/docs`.

## Sequência cronometrada

| Tempo | Ação e fala breve | Resultado esperado |
| --- | --- | --- |
| 0:00–0:45 | Mostrar `GET /health` e a navegação **Projetos / Cadastrar**. Explicar Streamlit → HTTPX → FastAPI → Service → Repository → SQLite e o banco Rev1 separado. | `status=ok`; em processo iniciado após a decisão D08, conferir versão `0.2.0` em `/health`; lista vazia ou dados de demonstração identificados, sem confundir health com verificação do banco. |
| 0:45–1:35 | Em **Cadastrar**, usar código `09.765`, subprojeto `03`, nomes “Projeto fictício” e “Piloto”, edição `DEMO-REV1-01`. Deixar equipe vazia e “Informar previsão de execução” desmarcado. Definir início de Seleção como ontem UTC; informar AP/AS/AD = **10/7/2** e clicar **Cadastrar projeto**. | Projeto em Seleção; Estoque = **3** e Executados = **5**, ambos calculados e somente leitura. Os zeros à esquerda dos dois códigos permanecem visíveis. |
| 1:35–2:15 | Em **Projetos**, selecionar pela combinação código/subprojeto/edição; mostrar listagem e **Detalhes e indicadores**. Em **Editar**, mudar as contagens para **8/8/8**, salvar e retornar aos detalhes. | Estoque e Executados tornam-se **0/0**; os três valores informados são editáveis, os dois derivados não. |
| 2:15–3:10 | Em **Workflow e histórico**, mostrar as cinco fases e confirmar Seleção → Desenvolvimento com data de hoje UTC. Mostrar os dois eventos do histórico. Em **Corrigir fase concluída**, selecionar Seleção e mudar sua data de ontem para hoje UTC; salvar. | A data de negócio concluída muda dentro do intervalo permitido; a sequência e o horário UTC de auditoria exibido continuam imutáveis. |
| 3:10–4:10 | Demonstrar o limite cronológico: a UI impede escolher data anterior ao mínimo da próxima fase. Na documentação da API, usar `POST /projects/{id}/phase` com `{"fase":"execucao","data_inicio_fase":"<ontem-em-YYYY-MM-DD>"}` para o projeto em Desenvolvimento. Reconsultar o histórico. | A API responde **422**; fase e número de eventos permanecem iguais. Substituir `{id}` e a data pelo ID criado e por ontem UTC; não enviar a data como texto literal. |
| 4:10–5:00 | Abrir **Excluir**, mostrar **Cancelar exclusão** e depois marcar **Confirmo a exclusão deste projeto** e clicar **Excluir definitivamente** apenas para o registro fictício criado. Atualizar a lista. | Cancelar preserva o registro; confirmar remove projeto e histórico. Nenhum projeto preexistente é excluído. |

## Fala de encerramento

A Rev1 permite editar campos e datas de fases concluídas no MVP; restringir isso total ou parcialmente é uma decisão possível **após** o MVP. O banco validado do projeto usa `projects.db` quando a API inicia pela raiz sem `DATABASE_URL`; o banco de demonstração separado não substitui esse arquivo. A troca futura para a Estratégia B deve preservar contratos e dados. A versão `0.2.0` foi autorizada e confirmada em `/health` e OpenAPI após reinício da API. Durante a demonstração, exibir novamente a versão em execução. O checklist foi aceito após 171 testes aprovados na suíte conjunta. CAP07-P01 revisou o Git e propôs commits por arquivo; commits e push seguem suas autorizações próprias, antes desta apresentação.

Se a apresentação não couber em cinco minutos, prepare o projeto fictício antes e mostre cadastro com um segundo registro fictício, mantendo a exclusão restrita ao registro criado para a demonstração. Registre o que foi efetivamente apresentado e quaisquer desvios no [checklist](checklist-entrega.md).