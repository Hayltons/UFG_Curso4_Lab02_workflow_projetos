# Revisão 1 do MVP — decisões e rastreabilidade

Registro iniciado em 03/10/2026 no CAP01-P02 e atualizado até o CAP06-P03 e a decisão posterior D08 em 05/10/2026. Este documento distingue decisões aprovadas, trabalho executado com evidência e pendências de entrega. Uma decisão isolada não comprova implementação; as seções CAP05/CAP06 registram as verificações efetivas.

## Contexto comum

Baseline: commit `1d358fd`, com FastAPI, SQLAlchemy/SQLite, Streamlit e HTTPX implementados. O registro de 42 testes aprovados pertence à baseline. No CAP05-P01, em 05/10/2026, 139 testes de backend/inicialização Rev1 passaram. No CAP05-P02, 32 testes de HTTPX/Streamlit passaram. No CAP05-P03, banco novo e integração automatizada real foram verificados; o usuário aceitou a integração/interface e o legado foi excluído. O usuário confirmou a execução básica da aplicação, com ajustes necessários.

Arquitetura mantida: navegador → Streamlit → HTTPX → FastAPI → Service → Repository → SQLite. O workflow permanece Seleção → Desenvolvimento → Execução → Pós-venda → Encerrado, com avanços sequenciais, entrada inicial no histórico e gravação atômica da fase, data e histórico. A Estratégia B fica para depois da conclusão do MVP.

## Decisões aprovadas pelo usuário

| ID | Decisão aprovada | Efeito a implementar depois |
| --- | --- | --- |
| D01 | Um registro por combinação de código do projeto, código do subprojeto e edição; manter `id` interno. | Chave única composta e seleção inequívoca mostrando os três valores; edição obrigatória conforme D02. |
| D02 | No cadastro, códigos e nomes do projeto e do subprojeto e edição são obrigatórios; equipe e data prevista para execução podem ficar vazias. | Códigos preservam zeros e edição participa da chave D01; equipe vazia e data ausente exigem contrato coerente; o banco novo começa vazio, sem inventar conteúdo. |
| D03 | AP = Selecionados, inteiro >0; AS = Avisados, inteiro >0 e ≤ Selecionados; AD = Descartados, inteiro >0 e ≤ Avisados. Os três são informados. | Validar inteiros estritos e relações no cadastro/PATCH. AD=AS é permitido e produz Executados=0. A regra antiga AP−AD fica substituída. |
| D04 | Estoque = Selecionados − Avisados; Executados = Avisados − Descartados. Ambos são inteiros calculados pelo Service e não editáveis. | `executados` substitui o campo e o rótulo Índice de Satisfação; não há percentual, Decimal ou arredondamento. Estoque e Executados podem ser zero. |
| D05 | Retirar descrição, conversão antiga e nota manual do contrato novo; não importar dados antigos, conforme D07 atualizada. Propor campos técnicos `selecionados`, `avisados`, `descartados`, `estoque` e `executados`. | Mudança coordenada de banco/API/UI. Os dados de teste antigos, inclusive `clientes_sensibilizados`, não serão transferidos nem reinterpretados. |
| D07 | Atualizada em 04/10/2026: iniciar a Rev1 com banco SQLite vazio e excluir o banco antigo de teste; dispensar migração, mapeamento e backup obrigatório. | CAP03-P06 executado em 05/10/2026: ferramenta retirada e orientação de inicialização ajustada, sem validação funcional naquela etapa. CAP05-P03 criou e validou `projects_rev1.db` em caminho distinto; `projects.db` foi excluído literalmente após aceite da integração e autorização específica. A frase sobre ausência de operação refere-se à atualização documental anterior. |
| D08 | Atualizar API e interface de forma coordenada, manter as rotas e PATCH; anunciar versão 0.2.0 somente após implementação e validação da Rev1. | Contrato/interface foram validados no CAP05. O usuário autorizou o anúncio de `0.2.0`; a constante da API foi atualizada. Após reinício autorizado, `/health` e OpenAPI confirmaram `0.2.0`; 1 projeto e 2 eventos permaneceram acessíveis. |

## D06 — edição de fases e auditoria

| ID | Resposta recebida | Ponto que precisa de confirmação antes da implementação |
| --- | --- | --- |
| D06 | No MVP Rev1, permitir editar campos de negócio do cadastro em fases já concluídas, inclusive suas datas de negócio. Datas sugeridas a partir do UTC e editáveis; ao abrir nova fase, início ≥ data da fase anterior e ≥ data UTC atual. | Corrigir data histórica somente se permanecer entre as datas das fases vizinhas, mantendo a cronologia; a exigência ≥ hoje vale ao abrir uma fase, não à correção histórica. A sequência/identidade das fases e os horários UTC de auditoria não são editáveis. Após o MVP, reavaliar restrição total ou parcial da edição de fases concluídas. |

D01–D08 estão aprovadas. D03/D04 incorporam as contagens inteiras e o campo Executados; D06 permite corrigir campos de negócio de fases concluídas, inclusive datas, mantendo horários UTC de auditoria imutáveis. A possível restrição dessa edição fica para avaliação pós MVP. A aprovação das decisões, isoladamente, não comprova implementação ou validação.

## Matriz M01–M12

A matriz foi iniciada no CAP01-P02 como plano. A coluna “Evidência” registra agora resultados CAP05/CAP06 ou pendências explícitas. As notas datadas de 04/10/2026 preservam o estado histórico anterior à implementação e à operação de banco.

| Mudança | Prompt(s) | Arquivo(s) previsto(s) | Aceite | Evidência |
| --- | --- | --- | --- | --- |
| M01 — Estado e decisões | CAP01-P01/P02, CAP02-P01 | `docs/revisao-rev1.md`, `docs/escopo-mvp.md`, `docs/backlog.md` | Baseline e decisões separadas de propostas. | CAP01-P01: inspeção de arquivos/Git; D01–D08 aprovadas e registradas. CAP03–CAP05 implementaram e validaram a Rev1; documentação/entrega seguem no CAP06. |
| M02 — Cadastro | CAP03-P01/P02, CAP04-P01/P02 | `app/models/project.py`, `app/services/project_service.py`, `app/repositories/project_repository.py`, `frontend/api_client.py`, `frontend/streamlit_app.py` | Códigos, nomes e edição obrigatórios; equipe e previsão opcionais; unicidade D01. | CAP05-P01: contratos de backend verificados. CAP05-P02: fluxos HTTPX/Streamlit verificados com mocks. CAP05-P03: usuário aceitou a integração/interface após solicitação de avaliação. |
| M03 — Indicadores | CAP01-P02, CAP03-P01/P02/P03 | `app/models/project.py`, `app/services/project_service.py`, `app/repositories/project_repository.py`, `app/api/project_routes.py` | Selecionados/AP, Avisados/AS e Descartados/AD são entradas; Estoque=AP−AS e Executados=AS−AD são inteiros calculados, somente leitura, inclusive zero. | CAP05-P01: indicadores de backend e contrato HTTP verificados, inclusive zeros. CAP05-P02: apresentação e ausência de edição dos derivados verificadas por AppTest. |
| M04 — Banco novo e descarte do legado | CAP02-P02, CAP03-P04/P06, CAP05-P01/P03 | `app/database.py`, `app/main.py`, remoção de `scripts/migrate_rev1.py`, `docs/banco-novo-rev1.md`, `tests/test_database_initialization_rev1.py` | Banco vazio no esquema Rev1; nenhuma importação; criação, execução e exclusão do antigo autorizadas separadamente. | CAP03-P06 executado em 05/10/2026: ferramenta retirada e orientação atualizada, com conferência estática. CAP05-P01: testes de inicialização aprovados em bancos isolados. CAP05-P03: `projects_rev1.db` criado vazio, esquema versão 1 e integridade verificados; dados fictícios persistiram após reinício. O `projects.db` legado foi excluído após aceite e autorização; em seguida, o arquivo Rev1 validado foi renomeado para `projects.db` e reaberto sem `DATABASE_URL`, preservando 1 projeto e 2 eventos. |
| M05 — Listagem e seleção | CAP04-P02 | `frontend/streamlit_app.py` | Todos os campos e escolha inequívoca por código/subprojeto/edição. | CAP05-P02: AppTest de listagem completa e seleção inequívoca passou. CAP05-P03: seleção confirmada com API real; usuário aceitou a interface. |
| M06 — Datas, fases e histórico | CAP03-P01/P02, CAP04-P02, CAP05-P01/P02 | `app/models/project.py`, `app/services/project_service.py`, `app/repositories/project_repository.py`, `frontend/streamlit_app.py`, testes | No MVP, corrigir campos de negócio e datas de fases concluídas, preservando cronologia e timestamps UTC de auditoria; nova fase ≥ anterior e ≥ hoje. | CAP05-P01: cronologia, edição histórica, auditoria e atomicidade verificadas no backend. CAP05-P02: datas editáveis, histórico, payload e auditoria somente leitura verificados por AppTest. CAP05-P03: avanço e correção histórica reais confirmados; usuário aceitou a interface. Restrição de edição reavaliável após MVP. |
| M07 — Erros e contratos | CAP03-P01/P03, CAP04-P01, CAP05-P01/P02 | `app/models/project.py`, `app/api/project_routes.py`, `frontend/api_client.py`, testes | 404/409/422 e PATCH coerentes com regras aprovadas. | CAP05-P01: OpenAPI e erros HTTP do backend verificados. CAP05-P02: cliente/interface verificaram 404/409/422, PATCH, timeout e ausência de repetição de escrita com mocks. |
| M08 — Qualidade | CAP05-P01/P02/P03 | `tests/test_project_service.py`, `tests/test_project_api.py`, `tests/test_api_client.py`, `tests/test_streamlit_app.py`, `tests/test_database_initialization_rev1.py` | Regressões e Rev1 verificadas sem usar banco local nos testes. | CAP05: 139 testes de backend/inicialização passaram no CAP05-P01 e 32 testes de HTTPX/Streamlit passaram no CAP05-P02; CAP05-P03 concluiu integração real, persistência após reinício, aceite do usuário e descarte autorizado do legado. A execução conjunta posterior aprovou 171 testes com quatro avisos de depreciação. |
| M09 — Documentação e entrega | CAP02-P01, CAP06-P01/P02/P03 | `docs/escopo-mvp.md`, `docs/backlog.md`, `README.md`, `docs/roteiro-demonstracao.md`, `docs/checklist-entrega.md` | Estado real, regras, banco novo/descarte, IA e commits descritos com evidências. | CAP06-P01 consolidou cópias; CAP06-P02 atualizou README, escopo, backlog e guias; CAP06-P03 criou roteiro e checklist. O anúncio de `0.2.0` foi autorizado depois e configurado no código; a versão foi confirmada em `/health` e OpenAPI após reinício; o usuário aceitou o checklist; a apresentação foi adiada para depois da publicação CAP07, e as operações de Git seguem suas autorizações próprias. |
| M10 — Materiais locais | CAP01-P03, CAP06-P01 | `.gitignore`, `README_Rev1.md` e três cópias auxiliares Rev1 | Originais preservados e materiais locais tratados conforme decisão. | CAP01-P03: regras de ignore presentes para os três auxiliares Rev1; CAP06-P01 consolidou as cópias. Por decisão do usuário, `README_Rev1.md` permanece local e não rastreado; a regra `/README_Rev1.md` foi incluída no `.gitignore` e confirmada com `git check-ignore -v`. |
| M11 — Versionamento | CAP07-P01/P02/P03 | Arquivos aprovados no diff final | Um arquivo por Conventional Commit; push somente autorizado. | CAP07-P01 revisou as mudanças e propôs commits por arquivo; CAP07-P02 registra os commits aprovados, um por arquivo, com hashes no relatório da etapa. O push permanece reservado ao CAP07-P03 e exige autorização própria. |
| M12 — Estratégia B | CAP06-P02, CAP08-P01 | `README.md`, `docs/backlog.md`, plano futuro da interface | Equivalência dos fluxos Rev1 depois da entrega do MVP. | README e backlog registram equivalência de códigos, edição, cinco contagens, datas e fases concluídas; planejamento/aceite da Estratégia B continuam para CAP08-P01. |

## Limites da atualização documental de 04/10/2026

Nenhum arquivo original protegido é alterado nesta atualização documental. Ela não autoriza implementação, leitura de dados locais, inicialização da aplicação, criação/exclusão de banco, testes, commit ou push.

## Atualização de D07 — 04/10/2026

O usuário escolheu iniciar com banco vazio e descartar o banco anterior, que contém somente dados de teste. Esta decisão substitui a migração offline aprovada anteriormente e a obrigação de preservar o legado em backup de D05. D01–D04, D06 e D08 permanecem vigentes.

CAP03-P05 foi executado para preparar a ferramenta, sem migrar banco real; passa a ser histórico, sem nova execução. A remoção de `scripts/migrate_rev1.py` e o ajuste da mensagem de inicialização ficam para CAP03-P06, com autorização própria. O procedimento vigente é [banco-novo-rev1.md](banco-novo-rev1.md); [migracao-rev1.md](migracao-rev1.md) passa a ser aviso histórico.

O conjunto documental desta decisão abrange os quatro arquivos Rev1, este registro, escopo, backlog e os dois documentos de banco. A autorização da escrita será obtida por parte; não significa aceite funcional. Em CAP05-P03, apresentar caminhos absolutos, criar e validar um arquivo novo distinto e só então autorizar a exclusão dos arquivos antigos identificados. Não há exigência de backup ou mapeamento de dados descartados. Registrar resultados efetivos; nenhuma dessas operações foi executada nesta revisão documental.

## CAP03-P06 — execução em 05/10/2026

**Decisão aplicada:** D07 atualizada, já aprovada pelo usuário: banco novo vazio e descarte posterior do legado de teste. D05 acompanha a dispensa de transferência/backup. As demais regras de negócio e a versão do esquema permanecem vigentes.

**Autorizações:** leituras e inspeção Git solicitadas por parte; edição dos dois trechos de `app/database.py` e exclusão literal de `scripts/migrate_rev1.py` autorizadas separadamente antes da execução. Atualização deste registro, do guia e do aviso histórico apresentada para autorização própria.

**Alterações realizadas:**

- `app/database.py`: comentário de SCHEMA_VERSION desvinculado do prompt de migração; SchemaCompatibilityError aponta para `docs/banco-novo-rev1.md` e para criação/descarte autorizados no CAP05-P03, com validação antes da exclusão.
- `scripts/migrate_rev1.py`: excluído; não estava rastreado pelo Git. O diretório não foi excluído.
- `docs/revisao-rev1.md`, `docs/banco-novo-rev1.md` e `docs/migracao-rev1.md`: estado e histórico atualizados.

**Verificações estáticas:** conteúdo de `app/database.py` comparado com o plano de duas substituições; restante do arquivo preservado. Confirmada ausência do script, hashes inalterados de `app/main.py` e `.env.example` e ausência de referências a `migrate_rev1`, `migracao-rev1` ou CAP03-P05 nos arquivos Python de app/frontend/tests/scripts. `git diff --check -- app/database.py` sem erros de whitespace; aviso de conversão futura LF/CRLF emitido pelo Git.

**Limites e aceite:** execução do CAP03-P06 concluída quanto às alterações e inspeção estática. Nenhum módulo foi importado para validar a aplicação; nenhum teste, instalação, inicialização de API/UI, acesso/criação/exclusão de banco, commit ou push foi executado. Lógica de compatibilidade, versão 1, constraints, regras de negócio e horários de auditoria preservados. Aceite funcional depende do CAP05; criação/execução do banco novo e descarte do antigo permanecem no CAP05-P03. Parada antes do CAP04-P01, sem autorização automática para o próximo prompt.

## CAP05-P01 — testes executados em 05/10/2026

**Escopo autorizado:** atualizar `tests/test_project_service.py` e `tests/test_project_api.py`, criar `tests/test_database_initialization_rev1.py` e executar somente esses três arquivos. A correção de código abaixo recebeu autorização separada. D01–D08 orientaram os casos; D07 foi verificada apenas em bancos isolados.

**Cenários:** campos obrigatórios/opcionais e limites; códigos ASCII com zeros; unicidade composta; inteiros estritos e relações das contagens; Estoque/Executados somente leitura, inclusive zero; PATCH conjunto; CRUD/404/409/422/204; OpenAPI; workflow sequencial; correções históricas entre datas vizinhas; auditoria UTC preservada; cascata; rollback após flush; persistência após reabertura. Inicialização cobre esquema vazio e versão, repetição sem alterações, bancos antigos/desconhecidos/parciais, divergências de estrutura, órfãos e falhas na criação das tabelas/marca de versão.

**Primeira execução:** 134 passaram e 5 falharam. A mesma sessão mantinha a relação de histórico desatualizada após uma transição: o registro existia no banco, mas a próxima operação do Service rejeitava a fase como inconsistente.

**Correção autorizada:** em `app/repositories/project_repository.py`, os eventos inicial e de transição passam a ser adicionados por `project.historico.append(...)`. Isso sincroniza a coleção carregada e a persistência. Nenhum teste válido foi removido para contornar a falha.

**Comando final (PowerShell, raiz do repositório):**

```powershell
$env:DATABASE_URL = "sqlite://"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONIOENCODING = "utf-8"
& .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_project_service.py tests/test_project_api.py tests/test_database_initialization_rev1.py
```

Variáveis usadas apenas no processo de execução; nenhuma configuração local persistente alterada. As fixtures utilizam SQLite em memória ou arquivos de `tmp_path`; o TestClient substitui engine e sessão antes do lifespan. Não houve leitura, criação ou exclusão dos bancos operacionais.

**Ambiente observado:** Windows, Python 3.11.6, SQLite 3.42.0, pytest 9.1.1, FastAPI 0.142.2, Pydantic 2.13.5, SQLAlchemy 2.1.2 e HTTPX 0.28.1.

**Resultado final:** `139 passed, 4 warnings in 3.42s`. Os quatro avisos de depreciação do Starlette referem-se ao uso de HTTPX no TestClient (um) e à constante HTTP_422_UNPROCESSABLE_ENTITY (três). Não foram instaladas ou atualizadas dependências nesta etapa.

**Verificações e aceite:** suíte solicitada aprovada; `git diff --check` sem erros nos arquivos verificados. Alterações preexistentes preservadas. O resultado cobre backend/inicialização, não representa aprovação funcional de toda a Rev1. Testes de HTTPX/Streamlit ficam no CAP05-P02; banco novo, descarte e avaliação real ficam no CAP05-P03. Não houve servidor HTTP externo, execução da UI, commit ou push. Parada antes do próximo prompt.


## CAP05-P02 — testes executados em 05/10/2026

**Escopo autorizado:** atualizar `tests/test_api_client.py` e `tests/test_streamlit_app.py` e executar somente essas duas suítes. A revisão de asserções e a reexecução receberam autorização própria. D01–D08 orientaram os casos; nenhum banco operacional foi acessado.

**Cenários HTTPX:** lista/detalhe com todos os campos Rev1 e zeros; POST/PATCH com datas ISO e somente entradas editáveis; mudança de fase, histórico e correção histórica; 404/409/422 estruturados, 500 sem exposição de detalhe interno, JSON inválido, indisponibilidade e timeout de POST/PATCH/DELETE sem retry; DELETE 204.

**Cenários AppTest:** lista vazia/completa e seleção inequívoca de edições do mesmo código; cadastro com campos obrigatórios e opcionais, inteiros e zeros, indicadores calculados somente leitura e envio único; datas de negócio no formato DD/MM/AAAA; data sugerida e editável da próxima fase; correção de fase concluída com identidade e auditoria UTC preservadas no payload; histórico, fase terminal, exclusão/cancelamento, 404/409/422, timeout e ausência de nova escrita em reruns. Limites de cronologia e regras relacionais são validados pela API nos testes do CAP05-P01.

**Comando final (PowerShell, raiz do repositório):**

```powershell
$env:DATABASE_URL = "sqlite://"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONIOENCODING = "utf-8"
& .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_api_client.py tests/test_streamlit_app.py
```

**Resultado final:** `32 passed in 2.53s`. Uma execução intermediária teve 31 aprovações e 1 falha causada por uma asserção que presumiu a posição da mensagem de timeout entre os textos da interface; a asserção foi corrigida e a suíte passou. O cliente usou `httpx.MockTransport`; o Streamlit usou `AppTest` com métodos da API simulados. Não houve rede externa, inicialização de servidor ou acesso a banco operacional.

**Limites e aceite:** CAP05-P02 concluído quanto aos testes automatizados solicitados. A validação visual/teclado, HTTP real, criação/execução do banco novo e descarte do antigo dependem do CAP05-P03 e de autorizações próprias. O aceite funcional da Rev1 permanece pendente. Nenhuma dependência foi instalada; nenhum commit ou push foi feito nesta etapa. Parada antes do próximo prompt.

## CAP05-P03 — operação parcial em 05/10/2026

**Decisão aplicada:** D07 aprovada: iniciar banco Rev1 vazio em arquivo novo e descartar o legado de teste somente após validação e aceite. O banco antigo foi identificado como `C:\1-TI\02_POS_GRADUACAO_UFG\05_Curso04_Lab02_Workflow\projects.db` (`user_version=0`, colunas legadas); `-wal`, `-shm` e `-journal` não existiam no inventário inicial. O destino `C:\1-TI\02_POS_GRADUACAO_UFG\05_Curso04_Lab02_Workflow\projects_rev1.db` estava ausente e é distinto. Nenhum registro do legado foi consultado ou importado.

**Operação autorizada:** servidores anteriores nas portas 8000/8501 foram identificados e encerrados. Com `DATABASE_URL=sqlite:///./projects_rev1.db`, a API foi iniciada na raiz do projeto usando `.venv/Scripts/python.exe -B -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. A UI foi iniciada com `API_BASE_URL=http://127.0.0.1:8000` usando `.venv/Scripts/python.exe -B -m streamlit run frontend/streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true`. As variáveis foram aplicadas somente aos processos, sem editar configuração local persistente.

**Banco vazio comprovado:** versão 1, tabelas `projects` e `phase_history`, colunas Rev1, 9 cláusulas CHECK na tabela de projetos, índice único, zero projetos e zero eventos, `PRAGMA foreign_key_check` vazio e `PRAGMA integrity_check=ok`. `GET /health` e `GET /projects` responderam 200; a lista estava vazia. O Streamlit respondeu HTTP 200 e AppTest com API real exibiu estado vazio.

**Integração real comprovada:** dois projetos fictícios com código `01.001`/subprojeto `01` e edições `REV1-DEMO-A` e `REV1-DEMO-B` foram criados pela interface. A listagem distinguiu as edições e mostrou todos os campos. As contagens `8/8/8` deram Estoque/Executados `0/0`; `10/7/2` deram `3/5`. No projeto A (ID 1), PATCH de título/equipe/previsão, transição Seleção→Desenvolvimento em 07/10/2026 e correção da data de Seleção para 06/10/2026 foram confirmados por GET, sem alterar a fase corrente nem timestamps UTC de auditoria. A API real retornou 404/409/422 para solicitações inválidas e preservou os dados; a UI exibiu 409/422 sem criação ou repetição por rerun. Cancelar a exclusão do projeto B preservou o registro.

**Reinício e persistência:** API e UI foram encerradas e iniciadas novamente com as mesmas URLs. Após o reinício, GET e leitura SQLite encontraram 2 projetos, 3 eventos históricos, versão 1 e integridade OK; a UI respondeu HTTP 200. Os servidores permanecem disponíveis localmente para avaliação. O arquivo `projects.db` ainda não foi excluído.

**Pendências e aceite:** aguardar avaliação do usuário no navegador, inclusive teclado e tela pequena, e seu aceite da integração. A exclusão real de um projeto fictício pela UI ainda não foi exercitada nesta operação; requer autorização própria e deve preservar dados Rev1 que o usuário queira manter. Só após o aceite, reinventariar o legado e pedir autorização explícita para excluir `projects.db` e eventuais auxiliares existentes. Não houve instalação, commit, push ou avanço ao CAP06.

## CAP05-P03 — conclusão em 05/10/2026

**Aceite do usuário:** após o pedido para avaliar a interface em `http://127.0.0.1:8501`, inclusive uso por teclado e em tela pequena, o usuário respondeu “Aceito a integração e a interface”. A resposta é o aceite manual; não há gravação independente de sessão de navegador, vídeo ou medições de acessibilidade.

**Exclusão de demonstração:** com autorização própria, `REV1-DEMO-B` (ID 2) foi excluído pela UI. A API passou a responder 404 para o ID 2; seu evento foi removido em cascata. `REV1-DEMO-A` (ID 1) e dois eventos históricos permanecem no banco novo.

**Descarte do legado:** inventário final mostrou apenas `C:\1-TI\02_POS_GRADUACAO_UFG\05_Curso04_Lab02_Workflow\projects.db` (24.576 bytes, última alteração 02/10/2026 11:26:30), sem auxiliares `-wal`, `-shm` ou `-journal`. A abertura exclusiva em leitura teve êxito. Após autorização explícita, somente esse caminho literal foi excluído, sem recursão, curingas ou backup. A conferência seguinte confirmou sua ausência e a presença de `projects_rev1.db`.

**Estado final verificado:** `projects_rev1.db` contém esquema versão 1, um projeto, dois eventos, `foreign_key_check` sem erros e `integrity_check=ok`. API e Streamlit responderam HTTP 200. `git check-ignore -v` confirmou `*.db` para o arquivo novo. Nenhum arquivo auxiliar antigo foi excluído porque nenhum existia. Os servidores locais permanecem ativos.

**Configuração operacional:** a API desta etapa usa `DATABASE_URL=sqlite:///./projects_rev1.db` definido no processo. O padrão do código e `.env.example` ainda apontam para `projects.db`; executar a API sem definir `DATABASE_URL` poderá criar outro banco vazio com esse nome. O README receberá instruções definitivas no CAP06-P02; mudar o padrão do código ou `.env.example` exige autorização própria. Não houve instalação, commit, push nem início do CAP06 neste prompt.

## Ajuste operacional posterior ao CAP05-P03 — nome padrão em 05/10/2026

Por solicitação do usuário, o banco Rev1 validado foi movido de `C:\1-TI\02_POS_GRADUACAO_UFG\05_Curso04_Lab02_Workflow\projects_rev1.db` para `C:\1-TI\02_POS_GRADUACAO_UFG\05_Curso04_Lab02_Workflow\projects.db`. Os servidores foram encerrados antes do movimento; destino e auxiliares SQLite estavam ausentes. O SHA-256 antes/depois foi `70C22C69CE98387285BCD64690B274B2A6B023FFC55BA76A893D2A4F2705B6B4`.

A API foi iniciada novamente **sem `DATABASE_URL`**, usando seu padrão `sqlite:///./projects.db`. GET real e leitura SQLite confirmaram esquema versão 1, 1 projeto fictício, 2 eventos, `foreign_key_check` vazio e `integrity_check=ok`. A interface respondeu HTTP 200 e foi reiniciada apontando para essa API. `projects_rev1.db` está ausente; `projects.db` está ignorado por `*.db` no Git. Os registros anteriores deste documento preservam o nome temporário usado na validação original; o nome operacional vigente é `projects.db`.
## CAP06-P03 — materiais de demonstração e checklist em 05/10/2026

**Arquivos criados com autorização própria:** `docs/roteiro-demonstracao.md` e `docs/checklist-entrega.md`. O roteiro usa dados fictícios em banco separado e cobre cadastro com equipe/previsão vazias, AP/AS/AD, Estoque/Executados inclusive zero, avanço sequencial, correção de data de fase concluída, auditoria UTC somente leitura, rejeição cronológica 422 e exclusão confirmada. Seu cronograma soma cinco minutos; a apresentação ainda não foi executada nesta etapa.

**Checklist:** RF-01 a RF-11, RNF-01 a RNF-06 e D01–D08 relacionados às evidências CAP05. O aceite do usuário para integração/interface foi registrado em CAP05-P03. Não há medição ou gravação independente de teclado/telas pequenas. A API anuncia `0.2.0-dev`; a versão final 0.2.0, a execução conjunta recomendada de `python -m pytest -q` e a revisão Git permanecem pendentes e exigem decisões/autorizações próprias. `README_Rev1.md` continua não rastreado e não ignorado; evitar inclusão acidental no CAP07.

**Verificações desta etapa:** leitura dos requisitos e evidências, inspeção estática dos formulários/rotas/regras de data, conferência das regras de `.gitignore` e do estado Git. Não foram iniciados API/UI, não houve alteração ou exclusão de banco, demonstração real, novos testes, instalação, commit ou push. Os materiais estão preparados para avaliação do usuário. CAP06-P03 não autoriza avançar ao CAP07 automaticamente.
## Decisão posterior D08 — anúncio de 0.2.0 em 05/10/2026

O usuário autorizou explicitamente o anúncio da versão final `0.2.0`. Em `app/main.py`, `APP_VERSION` foi alterada de `0.2.0-dev` para `0.2.0`; FastAPI/OpenAPI e `GET /health` usam essa constante. O teste de API compara o retorno com `APP_VERSION`, sem fixar a string antiga. README, escopo, backlog, checklist e roteiro de demonstração foram alinhados à decisão.

A observação `0.2.0-dev` nos registros CAP05/CAP06 anteriores é histórica. Nesta decisão, não houve reinício de API/UI nem consulta real de `/health`/OpenAPI; a confirmação de uma nova instância em execução permanece pendente e exige autorização própria. Não foram executados testes, instalação, operações de banco, stage, commit ou push. O anúncio autorizado não altera as pendências de avaliação do checklist, demonstração e revisão Git.
## Fechamento pré-commit — itens 1–4 em 05/10/2026

**Decisões e arquivos:** o usuário autorizou concluir os itens de fechamento e manter `README_Rev1.md` somente local. A regra exata `/README_Rev1.md` foi adicionada ao `.gitignore` e confirmada por `git check-ignore -v`; a cópia não foi removida nem incluída no Git. O aviso de incompatibilidade de esquema em `app/database.py` passou a orientar a escolha autorizada de outro SQLite vazio, sem sugerir que CAP05-P03 ainda esteja por executar; a asserção correspondente em `tests/test_database_initialization_rev1.py` foi ajustada. README, escopo, backlog, checklist e roteiro foram alinhados ao estado operacional observado.

**Verificação operacional:** a instância antiga da API, que anunciava `0.2.0-dev`, foi identificada na porta 8000 e encerrada. Com o processo parado, `projects.db` tinha 36.864 bytes, sem arquivos auxiliares SQLite, e SHA-256 `70C22C69CE98387285BCD64690B274B2A6B023FFC55BA76A893D2A4F2705B6B4`, igual ao hash documentado após o renomeio. A API foi reiniciada sem `DATABASE_URL`, usando o padrão `projects.db`. `GET /health` e OpenAPI informaram `0.2.0`; a API retornou 1 projeto e 2 eventos históricos, e o Streamlit respondeu HTTP 200. O hash não foi calculado após o reinício, pois o Windows manteve o arquivo aberto no processo da API.

**Limites e aceite:** a alteração do teste ainda não foi executada. A suíte conjunta `python -m pytest -q`, a apresentação, a inspeção independente por teclado/tela pequena e a avaliação deste checklist continuam pendentes. CAP07-P01 já apresentou proposta de commits por arquivo; ainda não houve stage, commit ou push neste fechamento. A confirmação da versão e a decisão sobre a cópia local não equivalem ao aceite final da entrega.

## Validação conjunta e aceite do checklist antes do CAP07-P02 — 05/10/2026

**Teste autorizado:** no ambiente virtual do projeto, `.venv\Scripts\python.exe -m pytest -q` terminou com `171 passed, 4 warnings in 7.22s`. Os quatro avisos são de depreciação de Starlette/FastAPI: uso de HTTPX no TestClient e constante `HTTP_422_UNPROCESSABLE_ENTITY`. Não houve falha nem instalação de dependências. A suíte conjunta incluiu a asserção de inicialização ajustada no fechamento anterior.

**Aceite e sequência:** o usuário aceitou explicitamente `docs/checklist-entrega.md` após ver o resultado. Escolheu executar a apresentação da aplicação conforme `docs/roteiro-demonstracao.md` somente após concluir os prompts CAP07 e publicar os commits. A apresentação e a inspeção independente por teclado/tela pequena ainda não ocorreram; o aceite do checklist não afirma que ocorreram. CAP07-P02 foi solicitado para commits separados por arquivo, enquanto o push permanece reservado ao CAP07-P03.

**Limites deste registro:** os 171 testes foram executados antes desta atualização documental. Nenhum teste foi repetido após as edições de documentação. Os hashes e o conjunto efetivo de commits devem ser conferidos no relatório de execução do CAP07-P02; nenhuma publicação é autorizada por esta nota.