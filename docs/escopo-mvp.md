# Escopo do MVP — Monitoramento de Projetos em Workflow

## 1. Objetivo

Disponibilizar uma aplicação web para gerenciar projetos conduzidos por equipes multidisciplinares e acompanhar sua evolução pelas fases **Seleção, Desenvolvimento, Execução, Pós-venda e Encerrado**.

A baseline implementou cadastro, consulta, edição, exclusão, workflow e histórico. A Rev1 redefiniu identificação, campos, contagens e datas; o banco novo foi criado e validado, e o legado de teste foi descartado com autorização. A interface Streamlit consome a API REST por HTTPX; os dados persistem em SQLite.

Este documento registra os requisitos aprovados e o estado comprovado da Rev1. Os 42 testes pertencem à baseline. No CAP05-P01 passaram 139 testes de backend/inicialização; no CAP05-P02, 32 de HTTPX/Streamlit. Depois, a suíte conjunta aprovou 171 testes com quatro avisos de depreciação. A integração/interface e o checklist foram aceitos pelo usuário. O roteiro foi preparado no CAP06-P03; a apresentação ocorrerá após a publicação dos prompts CAP07. O usuário autorizou o anúncio de `0.2.0`, confirmado em `/health` e OpenAPI após reinício da API.

## 2. Premissas e limites do MVP

- Back-end: Python 3.11+, FastAPI, Uvicorn e Pydantic v2.
- Persistência: SQLite com SQLAlchemy.
- Front-end do MVP (Nova Estratégia A): Streamlit com componentes nativos e cliente HTTPX síncrono para consumir a API REST. A Estratégia B — HTML5, CSS3, Bootstrap 5 e JavaScript ES6 com `fetch()` — fica como evolução após o MVP.
- Arquitetura: Navegador → servidor Streamlit → cliente HTTPX → API (Routes) → Service → Repository → Database. Models Pydantic definem e validam os contratos de entrada e saída.
- O Service concentra transições de fase e cálculo de indicadores; o Repository concentra a persistência.
- Testes executados com Pytest para domínio, API, inicialização e cliente HTTP, e AppTest para fluxos Streamlit; documentação com Swagger/OpenAPI e Mermaid; versionamento com Git/GitHub.
- Há um único workflow: projeto começa em Seleção e pode avançar somente para a fase seguinte da ordem apresentada. A mesma fase não pode ser submetida como transição e Encerrado é terminal, sem reabertura.
- Não há contas de usuário, autenticação ou permissões por perfil. A execução deve ocorrer em ambiente local ou interno controlado.
- Como convenção técnica, datas e horários gerados pelo servidor são registrados em UTC e expostos em ISO 8601 com fuso horário.
- A Rev1 mantém `GET /health`, CRUD, workflow, histórico e interface Streamlit com contrato atualizado. O startup protege o esquema Rev1 e recusa banco legado incompatível, sem migração automática.

## 3. Dados previstos

Os campos abaixo definem o contrato Rev1 aprovado e implementado (D01–D06). Códigos são texto para preservar zeros; edição participa da chave única. Campos derivados, fase e horários UTC de auditoria não são entradas comuns. O contrato foi coberto pelos testes CAP05-P01/P02 e pela integração aceita em CAP05-P03.

| Campo Rev1 | Regra aprovada |
| --- | --- |
| `id` | Identificador técnico estável, gerado pelo sistema. |
| `codigo_projeto` | Texto obrigatório NN.NNN (`^[0-9]{2}\.[0-9]{3}$`), preservando zeros. |
| `codigo_subprojeto` | Texto obrigatório NN (`^[0-9]{2}$`), preservando zeros. |
| `titulo` | Nome obrigatório do projeto, 1–150 caracteres. |
| `nome_subprojeto` | Nome obrigatório do subprojeto, 1–150 caracteres. |
| `edicao` | Texto obrigatório, 1–30 caracteres; integra a chave única com os dois códigos. |
| `equipe` | Texto opcional até 50 caracteres; pode ficar vazio. |
| `data_prevista_execucao` | Data de negócio opcional e editável. |
| `fase` | Fase atual controlada pelo workflow; edição comum não muda fase. |
| `data_inicio_fase` | Data de negócio editável, inclusive em fase concluída, respeitando cronologia. |
| `selecionados` (AP) | Inteiro estrito informado, >0. |
| `avisados` (AS) | Inteiro estrito informado, >0 e ≤ AP. |
| `estoque` | Inteiro calculado AP−AS, ≥0, somente leitura. |
| `descartados` (AD) | Inteiro estrito informado, >0 e ≤ AS. |
| `executados` | Inteiro calculado AS−AD, ≥0, somente leitura; substitui o antigo índice. |
| `criado_em`, `atualizado_em` | Horários UTC reais de auditoria, não editáveis. |

O histórico de fases possui registros associados ao projeto com fase de origem (nula na entrada inicial), fase de destino, data de negócio da fase e horário UTC real da mudança. Na Rev1, campos de negócio de fases concluídas, inclusive datas, podem ser corrigidos se mantiverem a ordem entre fases vizinhas. A sequência das fases e os horários UTC de auditoria não são editáveis. A criação registra a entrada inicial em Seleção; a exclusão remove o histórico em cascata na mesma transação.

O `status` retornado por `/health` informa a disponibilidade do processo HTTP; não representa a `fase` de um projeto.

## 4. Workflow

| Ordem apresentada no laboratório | Fase | Valor técnico adotado |
| --- | --- | --- |
| 1 | Seleção | `selecao` |
| 2 | Desenvolvimento | `desenvolvimento` |
| 3 | Execução | `execucao` |
| 4 | Pós-venda | `pos_venda` |
| 5 | Encerrado | `encerrado` |

```mermaid
flowchart LR
    S[Seleção] --> D[Desenvolvimento]
    D --> E[Execução]
    E --> P[Pós-venda]
    P --> F[Encerrado]
```

A ordem apresentada define a matriz adotada para o MVP: criação em Seleção e somente avanços para a fase imediatamente seguinte. Não são permitidos repetição, retorno ou salto; Encerrado é terminal. Esta é uma decisão de modelagem do projeto, pois o material do laboratório não especifica a matriz completa.

Regras já exigidas para o MVP:

- Registrar e exibir a fase atual.
- Alterar fase por uma operação específica, validada pelo Service.
- Registrar a data de cada mudança aceita e preservar seu histórico.
- Atualizar fase, data de entrada e histórico na mesma transação.
- Rejeitar transições inválidas conforme a matriz definida, sem alterar dados nem acrescentar histórico.
- Manter a mudança de fase separada da edição cadastral comum. No MVP Rev1, permitir correção de campos de negócio e datas de fases concluídas, preservando sequência, cronologia e horários UTC de auditoria. Uma restrição total ou parcial dessa edição poderá ser decidida após o MVP.

## 5. Requisitos funcionais (RF)

### RF-01 — Cadastrar projeto

A Rev1 deve cadastrar código do projeto (NN.NNN), código do subprojeto (NN), nomes do projeto e subprojeto e edição obrigatórios; equipe e previsão de execução podem ficar vazias. Informar Selecionados/AP, Avisados/AS e Descartados/AD como inteiros estritos nas relações RF-08. O sistema atribui `id`, registra horários UTC reais e inicia em Seleção.

**Aceite:** combinação código do projeto + código do subprojeto + edição é única; códigos preservam zeros; textos obrigatórios não aceitam branco; cadastro válido persiste após reinício; valores inválidos recebem erro por campo. Equipe e previsão ausentes são aceitas.

### RF-02 — Listar projetos

A Rev1 deve listar todos os campos de negócio solicitados, fase, datas e indicadores, com ID e horários técnicos identificados. A seleção usa código do projeto, subprojeto e edição para distinguir registros; uma base vazia mostra mensagem clara.

**Aceite:** todos os campos Rev1 aparecem; dois registros com o mesmo código do projeto continuam distinguíveis por subprojeto/edição; uma base vazia exibe mensagem sem erro.

### RF-03 — Consultar detalhes

A Rev1 deve consultar um projeto pelo `id`, exibindo identificação completa, campos opcionais, fase, datas de negócio, horários UTC de auditoria, três contagens informadas e Estoque/Executados calculados. O histórico permanece acessível conforme RF-07.

**Aceite:** um `id` existente retorna os dados e derivados corretos, inclusive zero; um `id` inexistente retorna HTTP 404 e mensagem compreensível na interface.

### RF-04 — Editar dados do projeto

A Rev1 deve editar por PATCH os campos cadastrais permitidos, incluindo códigos, nomes, edição, equipe opcional, previsão e Selecionados/AP, Avisados/AS e Descartados/AD. O Service valida o estado combinado, recalcula Estoque/Executados e atualiza `atualizado_em` com horário UTC real. Campos de negócio de fases concluídas, inclusive datas, podem ser corrigidos por operação específica; não mudar a fase corrente, a sequência nem horários UTC de auditoria.

**Aceite:** PATCH parcial válido persiste após reinício e mantém a fase; combinação inválida falha sem escrita parcial; derivados não aceitam edição direta. Correção de data histórica só é aceita entre datas das fases vizinhas, sem exigir que seja ≥ hoje.

### RF-05 — Excluir projeto

O sistema deve permitir excluir um projeto mediante confirmação explícita na interface. A exclusão remove também os registros de histórico associados, sem deixar referências órfãs.

**Aceite:** após a confirmação, o projeto deixa de aparecer na listagem e a consulta por seu `id` retorna HTTP 404; cancelar a confirmação não altera os dados.

### RF-06 — Movimentar projeto no workflow

O sistema deve oferecer somente o avanço à fase imediatamente seguinte; Encerrado é terminal. Ao abrir nova fase, a data de negócio sugerida em UTC é editável, mas deve ser ≥ data da fase anterior e ≥ data UTC atual. O Service valida a transição e registra fase, data de negócio, horário UTC real e histórico de forma atômica.

**Aceite:** cada mudança aceita persiste com data de negócio e horário UTC de auditoria; data anterior à fase anterior ou ao dia UTC atual é rejeitada. Transição inválida mantém fase e histórico intactos.

### RF-07 — Consultar histórico de fases

O sistema deve exibir o histórico de cada projeto em ordem do horário UTC de auditoria e ID, com origem, destino, data de negócio e horário real de cada mudança. No MVP Rev1, campos de negócio de fases concluídas, inclusive datas, são editáveis; horários de auditoria e sequência não são.

**Aceite:** entrada inicial e mudanças persistidas aparecem após reinício; correção histórica preserva cronologia e auditoria UTC. A ausência de registros é apresentada sem erro.

### RF-08 — Registrar e consultar indicadores operacionais

A Rev1 deve receber Selecionados (AP), Avisados (AS) e Descartados (AD) como inteiros estritos, com AP>0, 0<AS≤AP e 0<AD≤AS. O Service calcula Estoque=AP−AS e Executados=AS−AD como inteiros não editáveis; ambos podem ser zero. `executados` substitui o antigo Índice de Satisfação, sem percentual ou nota manual.


**Aceite:** rejeitar bool, fração, texto, zero nas três entradas e relações inválidas; aceitar AS=AP (Estoque=0) e AD=AS (Executados=0). POST/PATCH não aceitam Estoque/Executados como entrada; PATCH recalcula os dois derivados.

### RF-09 — Consultar estado da aplicação

O sistema deve disponibilizar `GET /health` com `status`, `version` e `timestamp` em UTC. Nesta versão, a rota informa que o processo HTTP está respondendo; não verifica a disponibilidade do banco de dados.

**Aceite:** a chamada retorna HTTP 200, `status` igual a `ok`, uma versão e um timestamp com informação de fuso horário. **Estado atual:** implementado.

### RF-10 — Associar equipe ao projeto

A Rev1 deve permitir informar, editar, limpar e exibir a equipe responsável em texto opcional de até 50 caracteres. Não criar entidade de pessoas ou equipes.

**Aceite:** equipe informada ou vazia permanece associada ao projeto e aparece em listagem, detalhes e edição sem criar valor fictício.

### RF-11 — Operar pela interface web

A interface Streamlit da Rev1 deve cobrir listagem completa, seleção por códigos/edição, cadastro, detalhes, edição, exclusão confirmada, workflow, histórico e correção de campos/datas de fases concluídas. Usa formulários com submissão explícita e cliente HTTPX para a API, sem acesso direto ao Service ou SQLite. Exibe Estoque/Executados recebidos da API, inclusive zero; não duplica cálculos. Após sucesso, a interface consulta dados atualizados; reexecuções comuns não repetem escritas.

**Aceite:** o usuário percorre os fluxos Rev1 no navegador, inclusive edição histórica, vê erros 404/409/422 e dados atualizados após sucesso; seleção, cancelamento e rerun não provocam escrita indevida.

## 6. Requisitos não funcionais (RNF)

### RNF-01 — Compatibilidade e execução

A aplicação deve executar com Python 3.11 ou superior, FastAPI, Uvicorn, Pydantic v2, Streamlit e HTTPX. As dependências e os comandos dos dois processos devem ser documentados no README: API na porta 8000 e interface na porta 8501. O cliente HTTP deve ler API_BASE_URL e definir timeout; não deve repetir automaticamente escritas após timeout. O ambiente local não exige banco remoto ou integrações de negócio externas.

### RNF-02 — Persistência e integridade

Projetos, três contagens informadas, dois derivados e histórico devem persistir em SQLite entre reinicializações. Unicidade composta D01, limites D02/D03 e cronologia D06 devem ser validados no contrato, Service e banco conforme cabível. Fase/data/histórico são atômicos; a exclusão do projeto remove seu histórico em cascata. Edição histórica não altera horário UTC de auditoria. D07 determina iniciar em banco vazio, sem importar dados antigos. Em CAP05-P03, um arquivo Rev1 distinto foi criado e validado; o banco antigo de teste foi excluído por caminho literal com autorização. O arquivo validado foi depois renomeado para o padrão `projects.db` e reaberto sem `DATABASE_URL`. Não exigir backup nem mapeamento. A inicialização cria o esquema apenas em banco vazio e recusa esquema incompatível, sem reset automático; `create_all()` não migra esquema. Não versionar bancos locais. Procedimento: [banco-novo-rev1.md](banco-novo-rev1.md).

### RNF-03 — Contrato da API

A API REST deve usar JSON e Models Pydantic v2 para validar entradas e respostas. Manter rotas existentes e PATCH; usar operação específica para corrigir campos de negócio de fase concluída. Usar 404 para ausentes, 409 para chave duplicada/transição inválida e 422 para validação. OpenAPI deve mostrar campos de entrada/saída e datas ISO. Erros não expõem SQL nem traceback; payload antigo não é presumido compatível.

### RNF-04 — Interface e acessibilidade básica

A interface deve funcionar em navegadores modernos, telas pequenas e por teclado. Campos e tabelas com muitos dados Rev1 precisam de rótulos, mensagens visíveis e indicação textual da fase, sem depender só de cor. AppTest não substitui avaliação visual e de teclado.

### RNF-05 — Segurança básica

Entradas devem ser validadas pela API. Dados fornecidos pelo usuário devem ser exibidos como texto nos componentes Streamlit, sem execução de HTML ou JavaScript. Segredos e configurações locais devem permanecer fora do controle de versão. Como não há autenticação, o MVP não deve ser exposto publicamente sem proteção adicional.

### RNF-06 — Manutenibilidade

O código Python deve usar tipos e separar Routes, Models, Service, Repository e Database. A UI separa apresentação e cliente HTTPX; não acessa SQLite nem duplica regras. O Service concentra validação de contagens, cronologia, workflow e derivados; o Repository preserva transações. Pytest/AppTest cobriram contratos Rev1, PATCH, inicialização/versão do esquema, histórico e edição de fases concluídas com auditoria UTC imutável nos CAP05-P01/P02. Consultas começam sem cache; diagramas usam Mermaid.

## 7. Fora de escopo

Exclusões expressas no laboratório:

- Autenticação.
- Controle de acesso.
- Integrações externas.
- Upload de arquivos.
- Dashboard analítico avançado.
- IA generativa como funcionalidade do produto.

Filtros de busca e contadores agregados por fase ficam para melhorias futuras. Os cinco campos de contagem, histórico e edição de campos de negócio de fases concluídas fazem parte da Rev1. A equipe continua texto opcional, sem gestão de usuários. Após o MVP, pode-se restringir total ou parcialmente a edição histórica por nova decisão.

## 8. Critério de conclusão do MVP

As decisões D01–D08 foram aplicadas ao código/API/UI; o banco Rev1 foi criado, validado e reaberto como `projects.db`, e o legado de teste foi descartado com autorização. Passaram 139 testes de backend/inicialização e 32 de HTTPX/Streamlit em suítes direcionadas; a suíte conjunta aprovou 171 testes com quatro avisos de depreciação. O usuário aceitou a integração/interface e o checklist. O README foi atualizado no CAP06-P02 e o roteiro foi preparado no CAP06-P03. A apresentação foi adiada para depois da publicação dos prompts CAP07; ainda não há registro independente de avaliação visual de teclado/telas pequenas. Por decisão explícita do usuário, a API anuncia `0.2.0`, confirmado em `/health` e OpenAPI após reinício, com 1 projeto e 2 eventos preservados. Isso não conclui a entrega.

## 9. Decisões de modelagem

| Decisão | Regra da Rev1 aprovada | Situação |
| --- | --- | --- |
| D01 | Unicidade por código do projeto + subprojeto + edição; `id` interno. | Implementada e verificada em CAP05. |
| D02 | Códigos/nomes de projeto e subprojeto e edição obrigatórios; equipe e previsão opcionais; limites da seção 3. | Implementada e verificada em CAP05. |
| D03 | AP=Selecionados>0; 0<AS=Avisados≤AP; 0<AD=Descartados≤AS, inteiros estritos informados. | Implementada e verificada em CAP05. |
| D04 | Estoque=AP−AS e Executados=AS−AD calculados, não editáveis e podendo ser zero; Executados substitui o antigo índice percentual. | Implementada e verificada em CAP05. |
| D05 | Retirar descrição, conversão e nota manual do novo contrato; descartar o legado de teste conforme D07, sem transferência ou reinterpretação. | Implementada; legado descartado no CAP05-P03. |
| D06 | Datas de negócio editáveis, inclusive de fases concluídas; nova fase ≥ anterior e ≥ hoje UTC; correção histórica entre vizinhas; horários UTC de auditoria imutáveis. | Implementada e verificada; restrição histórica reavaliável pós MVP. |
| D07 | Banco Rev1 vazio; excluir banco antigo de teste após validar o novo. Sem migração, mapeamento ou backup obrigatório. | Executada em CAP05-P03; banco validado renomeado para `projects.db`. |
| D08 | API/UI coordenadas, rotas e PATCH preservados; versão 0.2.0 apenas após validação. | Contrato/interface verificados; anúncio de `0.2.0` autorizado pelo usuário e confirmado em `/health` e OpenAPI após reinício. |

CAP03-P05 permanece histórico. CAP03-P06 retirou `scripts/migrate_rev1.py` e manteve a proteção contra esquemas incompatíveis; CAP05 verificou o comportamento. O banco legado de teste foi descartado, e o banco Rev1 ocupa agora o nome padrão `projects.db`.

## 10. Decisão técnica e Próximos Passos

A Nova Estratégia A com Streamlit foi adotada na baseline; a Rev1 atualizou contratos, dados e fluxos dessa arquitetura. As decisões D01–D08 foram aplicadas e verificadas nos CAP03–CAP05. A preparação da entrega prossegue no CAP06.

Após concluir e validar o MVP Rev1, migrar a interface para a Estratégia B: HTML5, CSS3, Bootstrap 5 e JavaScript ES6 consumindo a API FastAPI via `fetch()`. Reutilizar Models, Service, Repository, banco Rev1 e testes de backend. Preservar códigos/subprojetos/edição, cinco contagens, datas, workflow, histórico e a edição de fases concluídas enquanto essa regra estiver vigente; definir mesma origem ou CORS.

O aceite dessa evolução exige equivalência dos fluxos Rev1 e dados preservados sem Streamlit. A troca isolada da interface não exige nova migração de esquema. Após o MVP, reavaliar com o usuário se a edição de fases concluídas deve ser restringida total ou parcialmente; não aplicar essa mudança automaticamente.
