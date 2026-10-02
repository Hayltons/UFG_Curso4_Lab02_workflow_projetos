# Backlog — Nova Estratégia A

Decisão técnica: interface Streamlit, cliente HTTPX, API FastAPI, Pydantic v2, Service, Repository SQLAlchemy e SQLite. A referência original do laboratório usa HTML/Bootstrap/JavaScript; a adoção de Streamlit é uma adaptação do projeto para acelerar o MVP.

O escopo e os critérios funcionais estão em [escopo-mvp.md](escopo-mvp.md). Os itens abaixo somente podem ser concluídos quando a implementação e suas verificações existirem. As três releases do MVP precedem a Estratégia B.

## Release 1 — Core

| Estado | Item | Requisitos | Critério de aceite |
| --- | --- | --- | --- |
| Concluído | API inicial GET /health | RF-09 | Retorna status, versão e timestamp UTC. |
| Concluído | Adotar Nova Estratégia A no escopo | RF-11, RNF-01/06 | Streamlit → HTTPX → FastAPI documentado; B como evolução futura. |
| Concluído | Resolver modelagem e contratos | RF-01/04/05/06/07/08/10 | Registrar fase inicial, matriz de transições, histórico, exclusão, conversão, satisfação e limites dos campos. |
| Concluído | Manifestos e configuração | RNF-01/05 | Dependências compatíveis e API_BASE_URL documentadas; configurações locais ignoradas. |
| Concluído | Models, Service, Repository e banco | RNF-02/03/06 | Validação e regras separadas da persistência; dados sobrevivem à reinicialização. |
| Concluído | CRUD e equipe por API | RF-01/02/03/04/05/10 | Operações válidas persistem, inválidas são rejeitadas; equipe aparece nas respostas. |
| Concluído | Workflow e histórico atômico | RF-06/07, RNF-02 | Fase, datas e histórico na mesma transação; rejeição e falha não deixam alterações parciais. |
| Concluído | Indicadores | RF-08 | Entradas validadas e conversão calculada apenas no Service, conforme regra registrada. |
| Concluído | Cliente HTTPX | RNF-01/03/06 | URL configurável, timeout, tradução de erros e nenhuma repetição automática de escrita. |
| Concluído | Listagem, cadastro e detalhes Streamlit | RF-01/02/03/10/11 | Formulário com submissão explícita, seleção de projeto e estados vazios. |
| Concluído | Edição e exclusão Streamlit | RF-04/05/11 | Edição preserva fase; exclusão exige confirmação e pode ser cancelada. |
| Concluído | Workflow, histórico e indicadores Streamlit | RF-06/07/08/11 | Exibe dados da API e atualiza após sucesso; reexecuções comuns não repetem escritas. |

## Release 2 — Qualidade

| Estado | Item | Requisitos | Critério de aceite |
| --- | --- | --- | --- |
| Concluído | Testes do Service e workflow | RF-01/04/06/08 | Cobrir transições aceitas/rejeitadas, limites de indicadores e recálculo. |
| Concluído | Integridade e persistência | RF-05/07, RNF-02 | Cobrir rollback de fase/histórico, exclusão e persistência entre sessões. |
| Concluído | Testes de API | RF-01 a RF-10, RNF-03 | Contratos JSON, erros HTTP, projeto ausente, validação e healthcheck. |
| Concluído | Testes HTTPX e AppTest | RF-11, RNF-06 | Fluxos essenciais, erros/timeouts, confirmação e ausência de escritas repetidas por reexecução normal. |
| Pendente | Integração real e interface | RF-11, RNF-04/05 | API e Streamlit funcionam juntos; teclado, telas pequenas, rótulos e conteúdo textual conferidos. |

## Release 3 — Entrega Final

| Estado | Item | Requisitos | Critério de aceite |
| --- | --- | --- | --- |
| Concluído | README e arquitetura | RNF-01/06 | Estado real, instalação, dois processos, configuração, testes e diagrama documentados. |
| Pendente | Comandos auxiliares e exemplo de configuração | RNF-01/05 | run-api, run-ui e equivalentes PowerShell; .env.example coerente com o carregamento adotado. |
| Pendente | Demonstração em até cinco minutos | RF-01 a RF-11 | Mostrar CRUD, equipe, fases, histórico, indicadores e erro de transição. |
| Pendente | Checklist de entrega | Seção 8 do escopo | Evidências dos RF/RNF, decisões resolvidas e materiais locais ignorados. |

## Próximos Passos — Estratégia B

Esta evolução começa após a conclusão e validação do MVP. Não faz parte do aceite da Nova Estratégia A.

- [ ] Confirmar contratos REST para todos os fluxos.
- [ ] Criar HTML5/CSS3/Bootstrap 5/JavaScript ES6 e definir como servir os arquivos.
- [ ] Criar cliente fetch com tratamento de carregamento e erros equivalente.
- [ ] Migrar listagem, cadastro, detalhes, edição e exclusão confirmada.
- [ ] Migrar fase, datas, histórico e indicadores.
- [ ] Definir mesma origem ou CORS conforme a implantação.
- [ ] Verificar equivalência funcional, persistência e regras.
- [ ] Atualizar arquitetura, execução, dependências e demonstração.
- [ ] Retirar Streamlit e dependências exclusivas após o aceite; preservar HTTPX se usado nos testes.

Reutilizar API, Models, Service, Repository, SQLite e testes do back-end. Refazer telas, navegação, estado da interface e cliente HTTP. A troca isolada da interface não exige migração de dados. O aceite final exige todos os fluxos do MVP funcionando sem o processo Streamlit.

Verificação da interface, Service e API: 42 testes passaram. Falta conferir visualmente a interface no navegador, inclusive teclado e telas pequenas, e preparar a demonstração final.
