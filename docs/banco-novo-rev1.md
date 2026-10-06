# Banco novo da Rev1 — procedimento operacional

Atualizado em 05/10/2026. **CAP05-P03 concluído: banco Rev1 criado e validado, integração aceita e legado de teste excluído com autorização.**

## Decisão e alcance

O usuário optou por começar a Rev1 com banco SQLite vazio e excluir o banco antigo, que contém dados de teste. Não foram transferidos projetos, IDs, histórico, descrição, nota manual ou contagens antigas. Não há migração, mapeamento por ID ou backup obrigatório. A decisão substitui o plano anterior de [migração](migracao-rev1.md) e a preservação do legado prevista em D05.

As regras D01–D04, D06 e D08 permanecem em [revisao-rev1.md](revisao-rev1.md) e [escopo-mvp.md](escopo-mvp.md): entradas inteiras positivas Selecionados ≥ Avisados ≥ Descartados; Estoque e Executados calculados, inclusive zero; edição de campos/datas de fases concluídas no MVP; horários UTC de auditoria não editáveis.

Este procedimento trata somente do descarte inicial do legado de teste. Os dados criados na Rev1 devem persistir; repetir um prompt ou reiniciar a aplicação não autoriza apagá-los.

## Etapas e autorizações

| Etapa | Trabalho previsto | Limite |
| --- | --- | --- |
| Atualização documental / CAP02-P02 | Registrar decisão, configuração e procedimento. | Sem código, banco, startup ou testes. |
| CAP03-P05 — histórico | Ferramenta de migração já preparada sob a decisão anterior. | Não executar nem repetir; não houve migração real. |
| CAP03-P06 — executado em 05/10/2026 | `scripts/migrate_rev1.py` excluído e orientação de `app/database.py` ajustada para este guia. | Alterações autorizadas e conferidas estaticamente; sem criar/excluir banco, iniciar app ou testar. |
| CAP04 | Alinhar cliente HTTPX e interface ao contrato Rev1. | Autorizações de seus próprios prompts. |
| CAP05-P01/P02 — executados | Testes isolados de backend/inicialização e interface. | 139 + 32 testes passaram, sem usar banco operacional. |
| CAP05-P03 — executado | Banco Rev1 vazio criado/validado, API/UI e persistência verificadas, interface aceita, legado excluído. | Cada parte recebeu autorização própria; evidências ao final deste guia. |
| CAP06-P02 — executado | Consolidar documentação e README original. | Trechos aprovados e evidências reais aplicados aos documentos versionados. |

A escolha do descarte já está aprovada. As autorizações operacionais posteriores destinam-se aos comandos e caminhos concretos, sem tratar esta documentação como autorização de execução.

## Configuração e persistência

- `DATABASE_URL` configura o backend. O padrão atual é `sqlite:///./projects.db`, relativo à pasta de execução da API; esse padrão não foi alterado nesta revisão documental.
- `API_BASE_URL` configura o cliente HTTPX, normalmente `http://127.0.0.1:8000`.
- O projeto não carrega `.env` automaticamente. Uma alteração apenas nesse arquivo não configura o processo; definir a variável no terminal ou mecanismo de execução aprovado.
- No CAP05-P03, `projects_rev1.db` foi criado na raiz, distinto do antigo `projects.db`, que foi excluído após validação e aceite. Em seguida, o banco Rev1 validado foi renomeado para o nome padrão `projects.db`.
- Na criação inicial do CAP05-P03, os caminhos absolutos e a URL efetiva foram conferidos; o destino novo estava ausente. Na operação atual, `projects.db` já existe e deve ser reaberto, sem sobrescrever nem limpar.
- Fechar navegador, desligar processos ou desativar a venv não apaga dados confirmados. Reiniciar com a mesma URL/pasta deve reabrir o mesmo arquivo.
- Git pull não transfere bancos locais. Conferir regras de ignore antes da operação e antes de qualquer commit.

## Iniciar agora com o banco padrão

Execute pela raiz do repositório. Se o terminal ainda tiver `DATABASE_URL` temporária, remova-a antes de iniciar a API:

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Em outro terminal, inicie a interface:

```powershell
$env:API_BASE_URL = "http://127.0.0.1:8000"
python -m streamlit run frontend/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

O padrão `sqlite:///./projects.db` reabre o banco Rev1 validado nesta pasta. Em um clone sem banco local, o startup cria um banco Rev1 vazio com esse nome. `.env` não é carregado automaticamente. Em Linux/macOS, use `unset DATABASE_URL` e `export API_BASE_URL=http://127.0.0.1:8000`.

### Comandos históricos do CAP05-P03

Durante a validação, a API usou temporariamente `DATABASE_URL=sqlite:///./projects_rev1.db` e a interface usou o mesmo `API_BASE_URL`. Após o aceite, o banco legado foi excluído e o arquivo Rev1 validado foi renomeado para `projects.db`. O nome temporário não deve ser usado para a operação atual; a URL temporária e os resultados permanecem registrados na seção de evidências abaixo.
## Comportamento esperado da inicialização

A proteção de esquema do backend foi verificada em testes isolados do CAP05-P01 e no banco operacional novo do CAP05-P03:

- Banco vazio: criar tabelas/constraints Rev1 e registrar a versão do esquema; não semear projetos.
- Banco Rev1 compatível: validar versão e estrutura e manter os dados.
- Banco antigo, parcial, desconhecido ou com versão incompatível: recusar inicialização com orientação para este procedimento, sem transformar ou apagar dados.
- Não confiar somente em `PRAGMA user_version`; conferir estrutura e integridade referencial conforme implementação.
- `create_all()` não converte esquema antigo. Não adicionar reset, DROP ou exclusão automática ao startup.
- `/health` indica resposta do processo HTTP, não comprova sozinho banco íntegro ou persistência.

CAP03-P06 ajustou a mensagem de incompatibilidade para este guia e para as autorizações do CAP05-P03. Preservou a lógica de inicialização e SCHEMA_VERSION=1; a conferência foi estática, sem importar/executar a aplicação.

## CAP05-P03 — operação em partes autorizadas

### 1. Identificar arquivos e encerrar processos

Autorizar leitura da configuração efetiva e inventário de arquivos. Identificar banco antigo pelo caminho realmente usado, sem presumir que seja `projects.db`. Não é necessário consultar registros antigos para descartá-los. Qualquer inspeção adicional do SQLite exige autorização própria.

Apresentar caminhos absolutos do antigo, do novo e dos auxiliares existentes (`-wal`, `-shm`, `-journal`), identificar processos envolvidos e pedir autorização para encerrá-los. Confirmar destino distinto, ausente e dentro do diretório aprovado. Não apagar arquivos por extensão ou padrão genérico.

### 2. Criar o novo banco e conferir o estado vazio

Apresentar URL, comando e efeitos esperados; autorizar separadamente configuração e inicialização da API. O startup aprovado cria o esquema vazio. Autorizar as consultas de verificação: versão, tabelas/constraints, ausência de projetos/histórico e integridade referencial.

Se ocorrer falha ou surgir arquivo parcial, interromper e registrar seu estado. Não excluir/recriar automaticamente nem apagar o antigo. Uma nova tentativa exige analisar o arquivo já existente e aprovar o tratamento concreto.

### 3. Executar a aplicação e validar persistência

Autorizar o início da UI e as operações com dados fictícios de demonstração. Conferir estado vazio, cadastro, listagem completa, seleção por códigos/edição, campos opcionais, contagens, derivados inclusive zero, PATCH, workflow, histórico e correção de campos/datas concluídas sem editar auditoria UTC. Conferir erros e cancelamento/exclusão.

Autorizar encerramento e reinício com o mesmo banco e comprovar persistência por consultas reais. Registrar avaliação do usuário, teclado e telas pequenas. Testes automatizados aprovados não substituem essa avaliação. Limpeza de dados de demonstração, se desejada, precisa de autorização própria; não apagar todo o banco para realizá-la.

### 4. Excluir o banco antigo de teste

Somente após validar o novo banco e obter aceite da integração, apresentar a lista exata do banco antigo e de seus auxiliares ainda existentes. Conferir novamente que nenhum item é o banco novo ou seu auxiliar e que não há processo usando os arquivos antigos.

Solicitar autorização explícita para excluir esses caminhos com operação literal, sem recursão ou curingas. A decisão dispensa backup; não criar cópia/mapeamento por consequência deste passo. Depois da exclusão, os dados antigos não terão recuperação garantida. Se o arquivo antigo estiver ausente, registrar esse fato; não excluir outro arquivo como substituto.

Preservar o novo banco, inclusive dados de demonstração aprovados. O descarte não autoriza apagar outros bancos do projeto.

### 5. Registrar evidências e concluir

Autorizar atualização de `docs/revisao-rev1.md` com comandos, verificações realmente feitas, versão, resultado de estado vazio/integridade/reinício, avaliação, arquivos antigos excluídos e pendências, sem conteúdo sensível. Distinguir exclusão realizada de apenas autorizada.

Falhas mantêm a etapa pendente. Não prometer rollback para o legado após descartá-lo; correções posteriores devem preservar os dados Rev1. Testes, commits, push e início do próximo prompt não são consequências automáticas desta operação.

## Estado após CAP03-P06 — 05/10/2026

Ferramenta removida com autorização e orientação da inicialização atualizada. Conferidos conteúdo alterado, ausência do script e referências nos arquivos Python de app/frontend/tests/scripts; `app/main.py` e `.env.example` permaneceram iguais. Nenhum banco foi aberto, criado ou excluído, nenhuma aplicação foi iniciada e nenhum teste foi executado.

Este parágrafo registra o estado ao fim do CAP03-P06. O aceite funcional veio nos CAP05-P01/P02/P03; o banco Rev1 foi criado, a integração aceita e o legado descartado. Os 42 testes da baseline não validam a Rev1.


## CAP05-P03 — resultado operacional em 05/10/2026

**Caminhos:** o legado identificado foi `C:\1-TI\02_POS_GRADUACAO_UFG\05_Curso04_Lab02_Workflow\projects.db` (esquema antigo, `user_version=0`); o novo é `C:\1-TI\02_POS_GRADUACAO_UFG\05_Curso04_Lab02_Workflow\projects_rev1.db`. O destino estava ausente antes da inicialização. Nenhum `-wal`, `-shm` ou `-journal` do legado existia no inventário inicial ou final. Nenhum registro antigo foi lido ou importado.

**Criação e verificação:** a API iniciou com `DATABASE_URL=sqlite:///./projects_rev1.db`; o startup criou esquema versão 1, tabelas e constraints Rev1 sem projetos. Foram conferidos versão, colunas, índice único, 9 CHECKs na tabela de projetos, contagens `0/0`, `foreign_key_check` vazio e `integrity_check=ok`. `GET /health` e `GET /projects` responderam 200, e o Streamlit mostrou lista vazia.

**Integração e persistência:** dois registros fictícios com o mesmo código e edições diferentes permitiram conferir listagem/seleção, Estoque/Executados `0/0` e `3/5`, PATCH, previsão opcional, transição para Desenvolvimento, histórico, correção de fase concluída e auditoria UTC preservada. API e UI exibiram/rejeitaram 404/409/422 conforme o caso; cancelamento não apagou o registro. Após desligar e reiniciar os dois servidores com as mesmas URLs, ambos os registros e três eventos persistiram, com versão 1 e integridade OK. O usuário respondeu “Aceito a integração e a interface” ao pedido de avaliação de navegador, teclado e tela pequena.

**Exclusões autorizadas:** o registro fictício `REV1-DEMO-B` (ID 2) foi excluído pela UI, com cascata de seu histórico. O legado `projects.db` (24.576 bytes) foi aberto com exclusividade de leitura, depois removido por caminho literal e autorização específica, sem backup ou recursão. A conferência final encontrou legado ausente, novo banco presente com 1 projeto e 2 eventos, integridade OK e API/UI HTTP 200. `git check-ignore -v` confirmou que `projects_rev1.db` segue a regra `*.db`. O registro fictício A foi preservado.

**Limites:** a avaliação de teclado/tela pequena foi aceita pelo usuário; não há medição automática desses aspectos. Nenhuma dependência foi instalada, e não houve commit ou push. Este guia não autoriza apagar dados Rev1 em execuções futuras.

## Nome operacional após a validação — 05/10/2026

A pedido do usuário, o arquivo Rev1 validado foi renomeado de `projects_rev1.db` para **`projects.db`**, na raiz do repositório, com API/UI paradas e destino ausente. O SHA-256 foi preservado. O legado de teste que usava o mesmo nome havia sido excluído no CAP05-P03; o `projects.db` atual contém o esquema e os dados Rev1, não é o arquivo legado.

Uma nova API iniciada na raiz **sem `DATABASE_URL`** usou o padrão do código `sqlite:///./projects.db` e reabriu 1 projeto e 2 eventos, com versão 1 e integridade OK. O Streamlit foi reiniciado e respondeu HTTP 200. `projects_rev1.db` não existe mais. O arquivo atual continua ignorado pelo Git.

Para usar o banco padrão em um terminal que ainda tenha a variável temporária da validação, remova-a antes de iniciar a API:

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
& .venv/Scripts/python.exe -B -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Os comandos anteriores com `DATABASE_URL=sqlite:///./projects_rev1.db` registram a operação histórica do CAP05-P03; não são o comando vigente para o arquivo renomeado. Não excluir nem recriar o `projects.db` Rev1 em reexecuções.
