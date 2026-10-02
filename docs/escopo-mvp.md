# Escopo do MVP — Monitoramento de Projetos em Workflow

## 1. Objetivo

Disponibilizar uma aplicação web para gerenciar projetos conduzidos por equipes multidisciplinares e acompanhar sua evolução pelas fases **Seleção, Desenvolvimento, Execução, Pós-venda e Encerrado**.

O MVP contempla cadastro e consulta de projetos, alteração de fase com data e histórico, identificação da equipe responsável e indicadores operacionais. A interface Streamlit consome a API REST pelo servidor Python, usando HTTPX; os dados são persistidos em SQLite.

Este documento consolida o escopo funcional do laboratório. As convenções técnicas propostas e as regras não especificadas no material estão identificadas nas seções 3, 4 e 9; não devem ser confundidas com regras de negócio já aprovadas.

## 2. Premissas e limites do MVP

- Back-end: Python 3.11+, FastAPI, Uvicorn e Pydantic v2.
- Persistência: SQLite com SQLAlchemy.
- Front-end do MVP (Nova Estratégia A): Streamlit com componentes nativos e cliente HTTPX síncrono para consumir a API REST. A Estratégia B — HTML5, CSS3, Bootstrap 5 e JavaScript ES6 com `fetch()` — fica como evolução após o MVP.
- Arquitetura: Navegador → servidor Streamlit → cliente HTTPX → API (Routes) → Service → Repository → Database. Models Pydantic definem e validam os contratos de entrada e saída.
- O Service concentra transições de fase e cálculo de indicadores; o Repository concentra a persistência.
- Testes previstos com Pytest para domínio, API e cliente HTTP, e AppTest para fluxos essenciais do Streamlit; documentação com Swagger/OpenAPI e Mermaid; versionamento com Git/GitHub.
- Há um único workflow: projeto começa em Seleção e pode avançar somente para a fase seguinte da ordem apresentada. A mesma fase não pode ser submetida como transição e Encerrado é terminal, sem reabertura.
- Não há contas de usuário, autenticação ou permissões por perfil. A execução deve ocorrer em ambiente local ou interno controlado.
- Como convenção técnica, datas e horários gerados pelo servidor são registrados em UTC e expostos em ISO 8601 com fuso horário.
- O endpoint `GET /health` já existe; os demais requisitos funcionais abaixo descrevem o trabalho a implementar.

## 3. Dados previstos

Os nomes e contratos abaixo orientam a implementação adotada. Título e equipe são obrigatórios (1–200 caracteres), descrição é opcional (0–5000 caracteres), contagens começam em zero e não aceitam valores negativos, e satisfação é opcional de 0 a 10. A conversão usa duas casas decimais com arredondamento half-up.

| Campo proposto | Finalidade |
| --- | --- |
| `id` | Identificador único e estável, gerado pelo sistema. |
| `titulo` | Identificação textual do projeto. |
| `descricao` | Descrição da iniciativa. |
| `equipe` | Equipe multidisciplinar responsável, informada como texto; não é uma conta de usuário. |
| `fase` | Fase atual, restrita aos cinco valores da seção 4. |
| `data_entrada_fase` | Data e hora em que o projeto entrou na fase atual. |
| `alvos_planejados` | Quantidade inteira e não negativa de alvos planejados; valor padrão zero. |
| `clientes_sensibilizados` | Quantidade inteira e não negativa de clientes sensibilizados; valor padrão zero. |
| `indice_satisfacao` | Número opcional na faixa inclusiva de zero a dez. |
| `taxa_conversao` | Indicador calculado pelo Service; não informado manualmente pelo cliente. |
| `criado_em` | Data e hora de criação, geradas pelo servidor. |
| `atualizado_em` | Data e hora da última alteração, geradas pelo servidor. |

O histórico de fases possui registros associados ao projeto com fase de origem (nula na entrada inicial), fase de destino e data/hora da mudança, gerados pelo servidor. A criação registra a entrada inicial em Seleção. Na exclusão do projeto, seu histórico é excluído em cascata na mesma transação.

O `status` retornado por `/health` informa a disponibilidade do processo HTTP; não representa a `fase` de um projeto.

## 4. Workflow

| Ordem apresentada no laboratório | Fase | Valor técnico proposto |
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
- Rejeitar transições inválidas conforme a matriz que for definida, sem alterar os dados nem acrescentar histórico.
- Manter a mudança de fase separada da edição dos demais campos do projeto.

## 5. Requisitos funcionais (RF)

### RF-01 — Cadastrar projeto

O sistema deve permitir cadastrar projeto com título obrigatório, descrição opcional, equipe responsável obrigatória e dados de indicadores. Deve atribuir `id`, registrar datas e iniciar na fase Seleção.

**Aceite:** um cadastro válido aparece na listagem e permanece disponível após reiniciar a aplicação; dados inválidos produzem uma resposta de erro que identifica o campo afetado.

### RF-02 — Listar projetos

O sistema deve exibir os projetos cadastrados com, no mínimo, título, fase atual e equipe responsável. A listagem deve ter uma apresentação clara quando não houver projetos.

**Aceite:** projetos persistidos aparecem na interface; uma base vazia exibe mensagem de estado vazio, sem erro.

### RF-03 — Consultar detalhes

O sistema deve permitir consultar um projeto pelo `id`, incluindo seus dados, fase atual, data de entrada na fase, equipe e indicadores operacionais. O histórico deve estar acessível conforme RF-07.

**Aceite:** um `id` existente retorna o projeto correto; um `id` inexistente retorna HTTP 404 na API e uma mensagem compreensível na interface.

### RF-04 — Editar dados do projeto

O sistema deve permitir alterar os dados cadastrais, a equipe e os valores informados dos indicadores de um projeto existente. A edição deve aplicar as validações do contrato, atualizar `atualizado_em` e recalcular a taxa de conversão quando seus dados de entrada forem alterados.

**Aceite:** as alterações persistem após reiniciar a aplicação; a fase não é alterada pela edição comum e a taxa calculada não pode ser sobrescrita manualmente.

### RF-05 — Excluir projeto

O sistema deve permitir excluir um projeto mediante confirmação explícita na interface. A exclusão remove também os registros de histórico associados, sem deixar referências órfãs.

**Aceite:** após a confirmação, o projeto deixa de aparecer na listagem e a consulta por seu `id` retorna HTTP 404; cancelar a confirmação não altera os dados.

### RF-06 — Movimentar projeto no workflow

O sistema deve oferecer somente o avanço à fase imediatamente seguinte na ordem do workflow; Encerrado é terminal. O Service valida a transição independentemente da interface e registra fase, data de entrada, data de atualização e histórico de forma atômica.

**Aceite:** cada mudança aceita persiste com sua data e seu registro de histórico; uma transição rejeitada mantém a fase anterior e o histórico intactos.

### RF-07 — Consultar histórico de fases

O sistema deve permitir visualizar o histórico de mudanças de fase de cada projeto, em ordem cronológica, exibindo origem, destino e data/hora de cada mudança aceita.

**Aceite:** o histórico corresponde às mudanças persistidas e permanece disponível após reiniciar a aplicação. Projetos sem mudanças exibem um estado vazio compreensível.

### RF-08 — Registrar e consultar indicadores operacionais

O sistema deve permitir informar e consultar alvos planejados e clientes sensibilizados como contagens inteiras não negativas. O índice de satisfação é opcional, numérico, com faixa inclusiva de 0 a 10. O Service calcula a taxa como clientes sensibilizados ÷ alvos planejados × 100, arredondada a duas casas pelo método half-up; alvos iguais a zero produzem `null`, e valores acima de 100% são permitidos. Essa fórmula é decisão deste projeto, não exigência expressa do laboratório.


**Aceite:** valores válidos são persistidos; contagens negativas e satisfação fora da faixa inclusiva de 0 a 10 são rejeitadas; taxa é recalculada ao alterar qualquer contagem, é nula quando alvos são zero e pode superar 100%.

### RF-09 — Consultar estado da aplicação

O sistema deve disponibilizar `GET /health` com `status`, `version` e `timestamp` em UTC. Nesta versão, a rota informa que o processo HTTP está respondendo; não verifica a disponibilidade do banco de dados.

**Aceite:** a chamada retorna HTTP 200, `status` igual a `ok`, uma versão e um timestamp com informação de fuso horário. **Estado atual:** implementado.

### RF-10 — Associar equipe ao projeto

O sistema deve permitir informar, editar e exibir a equipe responsável em texto. Essa associação não exige cadastro de pessoas ou de equipes em entidades separadas.

**Aceite:** a equipe informada permanece associada ao projeto e aparece na listagem, nos detalhes e na edição.

### RF-11 — Operar pela interface web

O sistema deve oferecer telas de listagem, cadastro e edição, acesso à consulta e exclusão, visualização do workflow, histórico e indicadores. A navegação deve usar componentes nativos do Streamlit. As ações devem consumir a API REST pelo cliente HTTPX no servidor Streamlit, sem acesso direto da interface ao banco ou ao Service. Cadastro e edição devem usar formulários com submissão explícita; seleção e confirmações podem usar estado de sessão. Após sucesso, a interface deve consultar os dados atualizados. Reexecuções comuns não podem repetir operações de escrita.

**Aceite:** o usuário consegue executar os fluxos principais pelo navegador, visualizar erros retornados pela API e observar os dados atualizados após cada operação bem-sucedida.

## 6. Requisitos não funcionais (RNF)

### RNF-01 — Compatibilidade e execução

A aplicação deve executar com Python 3.11 ou superior, FastAPI, Uvicorn, Pydantic v2, Streamlit e HTTPX. As dependências e os comandos dos dois processos devem ser documentados no README: API na porta 8000 e interface na porta 8501. O cliente HTTP deve ler API_BASE_URL e definir timeout; não deve repetir automaticamente escritas após timeout. O ambiente local não exige banco remoto ou integrações de negócio externas.

### RNF-02 — Persistência e integridade

Os projetos, indicadores informados e registros de histórico devem permanecer disponíveis entre reinicializações, usando SQLite com SQLAlchemy. O histórico pertence ao projeto e é removido em cascata quando ele for excluído. Uma mudança de fase e seu histórico devem ser gravados na mesma transação. Falhas de escrita não podem deixar uma fase sem o registro correspondente. O arquivo SQLite local não deve ser versionado.

### RNF-03 — Contrato da API

A API REST deve usar JSON e Models Pydantic v2 para validar entradas e respostas. Deve empregar códigos HTTP coerentes: sucesso para operações válidas, 404 para projeto ausente e erro de validação ou conflito para dados e transições inválidos. Os contratos devem estar documentados em Swagger/OpenAPI. Mensagens de erro não devem expor detalhes internos do servidor ou do banco.

### RNF-04 — Interface e acessibilidade básica

A interface deve funcionar nas versões atuais de navegadores modernos, adaptar-se a telas pequenas e permitir operação por teclado. Campos de formulário devem ter rótulos, mensagens de erro visíveis e indicação textual da etapa, sem depender apenas de cor. A escolha de componentes nativos do Streamlit deve ser acompanhada de verificação real de teclado e telas pequenas.

### RNF-05 — Segurança básica

Entradas devem ser validadas pela API. Dados fornecidos pelo usuário devem ser exibidos como texto nos componentes Streamlit, sem execução de HTML ou JavaScript. Segredos e configurações locais devem permanecer fora do controle de versão. Como não há autenticação, o MVP não deve ser exposto publicamente sem proteção adicional.

### RNF-06 — Manutenibilidade

O código Python deve usar tipos e separar Routes, Models, Service, Repository e Database. A interface Streamlit deve separar apresentação e cliente HTTPX. O cliente deve centralizar URL, timeout e tratamento de erros; a interface não deve importar Repository, acessar SQLite ou duplicar regras do Service. O estado de sessão é temporário e não substitui persistência. As consultas de projetos começam sem cache para evitar dados desatualizados. Regras de workflow e cálculo de indicadores devem ficar no Service. Testes com Pytest devem cobrir CRUD, transições, atomicidade do histórico e indicadores; diagramas devem usar Mermaid.

## 7. Fora de escopo

Exclusões expressas no laboratório:

- Autenticação.
- Controle de acesso.
- Integrações externas.
- Upload de arquivos.
- Dashboard analítico avançado.
- IA generativa como funcionalidade do produto.

Filtros de busca e contadores agregados por fase não são exigidos pelo laboratório e ficam como melhorias futuras. O histórico de fases e os quatro indicadores operacionais fazem parte do MVP. A equipe em texto não implica gestão de usuários ou um cadastro independente de equipes.

## 8. Critério de conclusão do MVP

O MVP estará concluído quando as decisões da seção 9 estiverem registradas, RF-01 a RF-11 estiverem atendidos e os requisitos técnicos tiverem sido verificados. CRUD, equipe, workflow, histórico e indicadores devem funcionar pela interface Streamlit e API, persistir após reinicialização e ter os fluxos principais cobertos por testes. O README deve refletir os comandos de execução e as funcionalidades efetivamente entregues.

## 9. Decisões de modelagem

| Tema | Definição necessária antes da implementação correspondente |
| --- | --- |
| Interface | Decisão adotada: Nova Estratégia A com Streamlit → HTTPX → FastAPI. Estratégia B após o MVP. |
| Workflow | Decisão adotada: iniciar em Seleção; permitir apenas avanço à próxima fase; proibir repetição, retorno e salto; Encerrado terminal, sem reabertura. |
| Histórico | Decisão adotada: registrar criação como entrada inicial em Seleção, ordenar por timestamp e ID, excluir registros em cascata junto com o projeto. |
| Indicadores | Decisão adotada: sensibilizados/alvos × 100, duas casas half-up, sem resultado quando alvos = 0; valores acima de 100% permitidos. |
| Satisfação | Decisão adotada: valor opcional de 0 a 10, inclusive. |
| Contratos | Título e equipe obrigatórios com 1–200 caracteres; descrição opcional com até 5000 caracteres; contagens não negativas com padrão zero; satisfação opcional entre 0 e 10. Identificadores, fase inicial e timestamps são controlados pelo servidor. |

As decisões estão refletidas neste escopo e implementadas nos Models, Service, Repository, API, testes e interface Streamlit.

## 10. Decisão técnica e Próximos Passos

A Nova Estratégia A foi adotada para priorizar a entrega do MVP. O material original do laboratório permanece como referência: o uso de Streamlit é uma adaptação do projeto à orientação de HTML/Bootstrap/JavaScript. Essa decisão técnica não resolve automaticamente as regras de negócio pendentes da seção 9.

Após concluir e validar o MVP, migrar a interface para a Estratégia B: HTML5, CSS3, Bootstrap 5 e JavaScript ES6 consumindo a API FastAPI via `fetch()`. Reutilizar Models, Service, Repository, banco e testes do back-end. Refazer telas, navegação, estado da interface e cliente HTTP; definir mesma origem ou CORS conforme a implantação.

O aceite dessa evolução exige todos os fluxos do MVP funcionando sem o processo Streamlit e com dados e regras preservados. Somente então retirar a interface e suas dependências exclusivas. A migração não faz parte do critério de conclusão do MVP.