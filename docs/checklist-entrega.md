# Checklist de entrega — MVP Rev1

**Preparado em 05/10/2026 no CAP06-P03.** Este checklist organiza evidências já registradas e pendências de entrega. Criá-lo não executa demonstração, testes, alteração de versão, commit ou push. **Estado do aceite deste documento:** aceito pelo usuário após a suíte conjunta.

## Requisitos funcionais

| Requisito | Estado | Evidência e limite |
| --- | --- | --- |
| RF-01 — cadastro | Comprovado | CAP05-P01 validou códigos, textos, opcionais e unicidade; CAP05-P02 verificou formulário; CAP05-P03 criou projetos fictícios pela interface real. |
| RF-02 — listagem | Comprovado | Estado vazio, campos e seleção por código/subprojeto/edição verificados em AppTest e API/UI real. |
| RF-03 — detalhes | Comprovado | GET, dados/derivados e 404 verificados nos testes e na integração. |
| RF-04 — edição | Comprovado | PATCH conjunto, persistência e correção de fase concluída cobertos em testes e operação real; auditoria UTC preservada. |
| RF-05 — exclusão | Comprovado | Cancelamento preservou registro; exclusão fictícia `REV1-DEMO-B` foi confirmada pela UI, com 404 posterior e histórico removido. |
| RF-06 — workflow | Comprovado | Avanço sequencial, data mínima e transações testados; Seleção → Desenvolvimento exercitado com API/UI real. |
| RF-07 — histórico | Comprovado | Entrada inicial, avanço, correção histórica e persistência após reinício verificados. |
| RF-08 — indicadores | Comprovado | AP/AS/AD estritos e derivados somente leitura, inclusive Estoque/Executados = 0, cobertos nos testes e na integração. |
| RF-09 — health | Comprovado | `GET /health` respondeu 200; informa o processo HTTP, não a integridade do banco. Na operação CAP05, a versão observada era `0.2.0-dev`; após reinício autorizado, `/health` e OpenAPI confirmaram `0.2.0`. |
| RF-10 — equipe | Comprovado | Campo opcional e edição/limpeza verificados em testes; alteração com API real registrada no CAP05-P03. |
| RF-11 — interface | Comprovado com limite | AppTest e integração real cobriram fluxos; o usuário aceitou integração/interface. Não há gravação independente da sessão visual ou medição de teclado/telas pequenas. |

## Requisitos não funcionais

| Requisito | Estado | Evidência e limite |
| --- | --- | --- |
| RNF-01 — execução | Comprovado no Windows | API/UI rodaram localmente em Python 3.11; [README](../README.md) traz instalação e comandos Windows/Linux/macOS. Execução em Linux/macOS não foi registrada. |
| RNF-02 — persistência/integridade | Comprovado | Banco Rev1 criado vazio, esquema versão 1, integridade referencial, reinício com dados preservados e recusa de incompatíveis verificados. |
| RNF-03 — contrato API | Comprovado | Modelos, OpenAPI, PATCH e respostas 404/409/422 cobertos nos testes CAP05-P01/P02 e na integração. |
| RNF-04 — acessibilidade básica | Parcial | Rótulos e mensagens cobertos por AppTest; houve aceite manual da interface. Inspeção independente por teclado e em tela pequena ainda não tem registro. |
| RNF-05 — segurança básica | Parcial | Validação de entradas e execução local/interna estão previstas e exercitadas. Revisão final de segredos e arquivos incluídos no Git fica no CAP07; o MVP não tem autenticação. |
| RNF-06 — manutenibilidade | Comprovado no escopo Rev1 | Camadas Routes/Models/Service/Repository e cliente HTTPX separados; testes focalizados passaram. A suíte conjunta posterior aprovou 171 testes, com quatro avisos de depreciação. |

## Decisões, banco e testes

- [x] **D01 e D02:** chave composta; códigos/nomes/edição obrigatórios, equipe e previsão opcionais; verificados em CAP05.
- [x] **D03 e D04:** AP/AS/AD informados e Estoque/Executados calculados, inclusive zero; verificados em CAP05.
- [x] **D05:** descrição, conversão antiga e nota manual retiradas do novo contrato, sem importação de dados legados.
- [x] **D06:** campos e datas de fases concluídas editáveis no MVP, com cronologia e auditoria UTC preservadas; possível restrição futura permanece para decisão após o MVP.
- [x] **D07:** banco Rev1 criado vazio, legado de teste excluído por caminho literal e autorização específica; ferramenta de migração retirada.
- [x] **D08 — anúncio da versão:** API e interface foram alinhadas e aceitas, com rotas/PATCH preservados. O usuário autorizou `0.2.0` e a constante da API foi atualizada.
- [x] **Confirmar versão em execução:** após reinício autorizado, `/health` e OpenAPI informaram `0.2.0`; a API preservou 1 projeto e 2 eventos.
- [x] **Banco vigente:** arquivo validado renomeado para `projects.db`, reaberto sem `DATABASE_URL`; 1 projeto fictício, 2 eventos, esquema versão 1 e `integrity_check=ok` na última conferência registrada. Banco local ignorado pelo Git.
- [x] **Persistência:** dados permaneceram após reinício de API/UI no CAP05-P03; o renomeio preservou SHA-256 e a API reabriu o mesmo conteúdo.
- [x] **Testes Rev1 executados:** 139 de backend/inicialização no CAP05-P01 e 32 de HTTPX/Streamlit no CAP05-P02, em suítes separadas e bancos isolados/mocks. Os 42 testes da baseline são apenas históricos.
- [x] **Suíte conjunta executada:** `.venv\Scripts\python.exe -m pytest -q` aprovou 171 testes em 7,22 segundos, com quatro avisos de depreciação.
- [x] **Revisão humana:** o usuário respondeu “Aceito a integração e a interface” no CAP05-P03.
- [ ] **Demonstração e inspeção visual independente:** [roteiro de até cinco minutos](roteiro-demonstracao.md) preparado; por escolha do usuário, a apresentação ocorrerá após a publicação dos prompts CAP07. Teclado e tela pequena ainda não foram avaliados de modo independente. Usar dados fictícios e banco separado.
- [x] **Documentação:** [README](../README.md), [escopo](escopo-mvp.md), [backlog](backlog.md), [procedimento do banco](banco-novo-rev1.md) e [decisões/evidências](revisao-rev1.md) descrevem a Rev1. O plano de [migração](migracao-rev1.md) permanece histórico.
- [x] **Adaptação acadêmica:** a Nova Estratégia A com Streamlit/HTTPX substituiu no MVP a interface HTML/Bootstrap/JavaScript da referência; a Estratégia B está documentada como evolução posterior, com equivalência das regras Rev1.
- [x] **Banco e três auxiliares locais ignorados:** `projects.db`, cópias Rev1 da estratégia, das recomendações de modelo e do roteiro de prompts seguem regras de `.gitignore` verificadas.
- [x] **`README_Rev1.md` local:** por decisão do usuário, a cópia de avaliação permanece local; `/README_Rev1.md` foi incluído no `.gitignore` e a regra foi confirmada com `git check-ignore -v`.
- [x] **Aceite do checklist:** o usuário aceitou este documento após a execução da suíte conjunta.
- [ ] **Publicação:** CAP07-P02 registra os commits por arquivo aprovado; o push depende de autorização própria no CAP07-P03.

## Critério para encaminhar

O checklist foi **aceito pelo usuário** após a suíte conjunta de 171 testes. O anúncio de `0.2.0` foi confirmado em `/health` e OpenAPI após reinício. `README_Rev1.md` permanece local e ignorado; CAP07-P01 revisou o conjunto Git. A demonstração e a inspeção visual independente continuam pendentes para depois da publicação; Os commits por arquivo são conferidos no relatório CAP07-P02; CAP07-P03 exige autorização própria para o push.