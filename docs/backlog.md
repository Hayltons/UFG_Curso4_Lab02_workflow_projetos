# Backlog — revisão 1 da Nova Estratégia A

A [baseline do MVP](escopo-mvp.md) já usa Streamlit → HTTPX → FastAPI → Service → Repository → SQLite. As decisões D01–D08 estão registradas em [revisao-rev1.md](revisao-rev1.md). Este backlog separa a baseline, as mudanças Rev1 já implementadas e verificadas e as etapas de entrega ainda pendentes.

**Estados:** “Concluído na baseline” descreve a versão anterior; “Concluído na Rev1” indica implementação e evidência CAP05; “Pendente” depende de etapa posterior. Os 42 testes históricos não validam a Rev1. Passaram 139 testes de backend/inicialização e 32 de HTTPX/Streamlit em suítes direcionadas; depois, a suíte conjunta aprovou 171 testes com quatro avisos de depreciação. Banco e integração foram validados, e o checklist foi aceito pelo usuário. O usuário autorizou `0.2.0`; `/health` e OpenAPI confirmaram a versão após reinício da API, com 1 projeto e 2 eventos preservados. Esta atualização documental não executa testes, banco, commits ou push.

## Baseline implementada — histórico

| Estado | Entrega existente | Evidência e limite |
| --- | --- | --- |
| Concluído na baseline | API FastAPI, `GET /health`, CRUD/PATCH, Service, Repository e SQLite | Rotas e persistência existentes; o contrato de contagens ainda é o anterior. |
| Concluído na baseline | Workflow sequencial, histórico inicial, transações e exclusão em cascata | Cinco fases e regras de avanço existentes; edição histórica Rev1 ainda não entregue. |
| Concluído na baseline | Streamlit e cliente HTTPX | Listagem, formulários, consulta, edição, exclusão e fases já existem com campos antigos. |
| Concluído na baseline | Testes automatizados registrados | 42 aprovados historicamente; nenhum teste Rev1 foi executado nesta etapa. |
| Concluído na baseline | README de instalação e execução | Clone/pull e dois processos documentados; regras Rev1 ainda não aplicadas ao original. |

## Revisão 1 — Core

| Estado | Item | Requisitos/decisões | Critério de aceite e etapa |
| --- | --- | --- | --- |
| Concluído na Rev1 | Atualizar escopo e backlog | D01–D08; RF/RNF Rev1 | CAP02-P01 registrou decisões e requisitos; CAP06-P02 alinhou estados às evidências reais. |
| Concluído na Rev1 | Contratos de cadastro e unicidade | D01/D02; RF-01/02/03/04/10 | Códigos NN.NNN/NN, nomes e edição obrigatórios; equipe/previsão opcionais; limites 150/30/50; chave única composta e ID interno. CAP03-P01/P02/P03. |
| Concluído na Rev1 | Contagens e derivados | D03/D04/D05; RF-08 | AP=Selecionados>0; 0<AS=Avisados≤AP; 0<AD=Descartados≤AS. Estoque=AP−AS e Executados=AS−AD inteiros, somente leitura; AD=AS e Executados=0 válidos. Nota/conversão/descrição removidas do contrato; legado descartado sem importação no CAP05-P03. CAP03-P01/P02/P03 e CAP05-P01/P03. |
| Concluído na Rev1 | Datas e edição de fases concluídas | D06; RF-04/06/07 | Nova fase tem data ≥ anterior e ≥ hoje UTC. Corrigir campos de negócio e datas históricas entre fases vizinhas, sem alterar sequência nem horários UTC de auditoria; persistência atômica. CAP03-P01/P02/P03. |
| Concluído na Rev1 | Plano de banco novo e configuração | D05/D07; RNF-01/02 | `docs/banco-novo-rev1.md` registra o procedimento, o descarte autorizado e a reabertura do banco validado em `projects.db`. CAP02-P02, CAP05-P03 e CAP06-P02. |
| Concluído na Rev1 | Esquema e retirada da ferramenta de migração | D01–D07; RNF-02/03 | CAP03-P06 retirou a ferramenta; CAP05-P01 verificou criação em banco vazio, recusa de incompatível e ausência de reset. CAP03-P05 permanece histórico. |
| Concluído na Rev1 | API e cliente HTTPX Rev1 | D08; RF-01 a RF-08, RNF-03 | Manter rotas/PATCH existentes; expor campos novos, correção histórica, 404/409/422, OpenAPI e mensagens úteis sem repetir escritas. CAP03-P03, CAP04-P01. |
| Concluído na Rev1 | Interface Streamlit Rev1 | D01–D06; RF-01 a RF-11, RNF-04/06 | Listar todos os campos, selecionar por códigos/edição, permitir formulários e correção histórica, exibir derivados da API e datas, preservar confirmações e estado vazio. CAP04-P02. |

## Revisão 1 — Qualidade

| Estado | Item | Requisitos/decisões | Critério de aceite e etapa |
| --- | --- | --- | --- |
| Concluído na Rev1 | Testes de Service, API e inicialização | D01–D08; RNF-02/03/06 | Pytest em bancos isolados cobre limites, zero válido, PATCH, unicidade, datas, auditoria imutável, atomicidade, esquema/versão, banco vazio/compatível/incompatível e ausência de reset automático em `tests/test_database_initialization_rev1.py`. 139 testes aprovados em CAP05-P01, em bancos isolados. Comandos/resultados em `revisao-rev1.md`. CAP05-P01. |
| Concluído na Rev1 | Testes HTTPX e Streamlit | RF-11; RNF-04/06 | 32 testes com AppTest/mocks aprovados em CAP05-P02, cobrindo fluxos Rev1, erros, PATCH, seleção, edição histórica, cancelamento e ausência de escrita em rerun. |
| Concluído na Rev1 | Suíte conjunta | RNF-06 | `.venv\Scripts\python.exe -m pytest -q`: 171 testes passaram em 7,22 segundos, com quatro avisos de depreciação. |
| Concluído na Rev1 | Inicialização em bancos isolados | D07; RNF-02 | Criação, versão/estrutura, recusa de banco antigo/parcial/desconhecido, atomicidade e reinício sem perda cobertos em bancos isolados. CAP05-P01. |
| Concluído na Rev1 | Banco vazio, integração real e descarte autorizado | D07/D08; RF/RNF Rev1 | CAP05-P03 criou e validou banco distinto, API/UI, reinício e exclusão literal do legado após aceite; arquivo validado renomeado e reaberto como `projects.db`, com 1 projeto e 2 eventos. |
| Concluído na Rev1 | Aceite da integração/interface | RF-01 a RF-11; RNF-04 | Usuário aceitou integração e interface no CAP05-P03. Não há registro independente de inspeção visual de teclado e telas pequenas; demonstrar ou registrar limite no CAP06-P03. |

## Revisão 1 — Entrega Final

| Estado | Item | Requisitos/decisões | Critério de aceite e etapa |
| --- | --- | --- | --- |
| Concluído na Rev1 | Consolidar cópias e README | D01–D08; RNF-01/06 | CAP06-P01 consolidou as quatro cópias; CAP06-P02 aplicou o README Rev1 com comandos, banco novo/descarte, regras e evolução pós MVP. |
| Concluído na Rev1 | Escopo, backlog e procedimento de banco | RNF-02/03 | CAP06-P02 registrou resultados de testes, banco e descarte, mantendo links para documentos versionados. |
| Concluído na Rev1 | Roteiro e checklist de entrega | RF-01 a RF-11; RNF aplicáveis | CAP06-P03 preparou roteiro de até cinco minutos e checklist de evidências e pendências. |
| Concluído na Rev1 | Aceite do checklist | RF-01 a RF-11; RNF aplicáveis | Usuário aceitou o checklist de entrega após a suíte conjunta. |
| Pendente | Apresentação e inspeção visual | RF-01 a RF-11; RNF aplicáveis | Usuário optou por demonstrar a aplicação depois da publicação dos prompts CAP07; teclado e tela pequena ainda não têm registro independente. |
| Concluído na Rev1 | Confirmar versão 0.2.0 em execução | D08 | Após reinício autorizado, `/health` e OpenAPI informaram `0.2.0`; a API preservou 1 projeto e 2 eventos. |
| Pendente | Publicação dos commits | Entrega aprovada | CAP07-P01 revisou o Git; CAP07-P02 registra um commit por arquivo aprovado. O push fica no CAP07-P03, com autorização própria e sem materiais locais. |

## Melhoria opcional após o MVP

- [ ] Avaliar Makefile ou scripts `run-api`/`run-ui` e equivalentes PowerShell. Os comandos atuais já estão documentados; esses atalhos não condicionam o aceite da Rev1.
- [ ] Reavaliar com o usuário se a edição de campos e datas de fases concluídas deve ser restringida total ou parcialmente. Até nova decisão, preservar a permissão do MVP e manter horários UTC de auditoria imutáveis.

## Próximos Passos — Estratégia B

A migração da interface para HTML5, CSS3, Bootstrap 5 e JavaScript ES6 via `fetch()` começa somente após conclusão e validação do MVP. A troca isolada da interface não exige outra migração de esquema.

- [ ] Planejar telas e cliente `fetch()`, incluindo estados vazios, erros, carregamento e confirmação de exclusão. CAP08-P01.
- [ ] Preservar API e banco; códigos de projeto/subprojeto, nomes e edição; Selecionados/AP, Avisados/AS, Descartados/AD, Estoque e Executados; previsão e datas das fases, workflow e histórico. Manter a edição de fases concluídas enquanto vigente e preservar horários UTC de auditoria.
- [ ] Definir mesma origem ou CORS conforme a implantação e comparar todos os fluxos com a Rev1.
- [ ] Atualizar execução, arquitetura e testes; retirar Streamlit somente após aceite e verificar uso de HTTPX nos testes.

CAP03–CAP05 foram concluídos com as autorizações de cada operação. CAP06-P03 preparou os materiais de entrega e CAP07-P01 revisou as mudanças e propôs commits por arquivo. CAP07-P02 trata os commits aprovados por arquivo; CAP07-P03 trata a publicação com autorização própria. A apresentação ocorrerá após a publicação, e a Estratégia B permanece posterior à conclusão do MVP.
