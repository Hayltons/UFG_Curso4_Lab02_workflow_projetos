# Migração Rev1 — plano substituído

Atualizado em 05/10/2026. **Registro histórico; não executar a ferramenta nem o procedimento anterior.**

## Decisão vigente

O usuário optou por iniciar a Rev1 com banco vazio; o banco antigo de teste foi excluído com autorização no CAP05-P03. D07 substitui a migração offline; D05 deixa de exigir preservação do legado em backup. Não há transferência de projetos/IDs/histórico, mapeamento por ID ou backup obrigatório.

O procedimento atual está em [banco-novo-rev1.md](banco-novo-rev1.md), com rastreabilidade em [revisao-rev1.md](revisao-rev1.md).

## Histórico da decisão e da operação

- CAP02-P02 preparou o plano de migração sob a decisão anterior.
- CAP03-P05 preparou `scripts/migrate_rev1.py`. A ferramenta não foi executada para migrar o banco real e não recebeu testes funcionais da Rev1; a verificação de sintaxe não é evidência funcional.
- CAP03-P05 permanece no roteiro como histórico, sem nova execução.
- CAP03-P06 executado em 05/10/2026: `scripts/migrate_rev1.py` excluído com autorização; comentário e mensagem de `app/database.py` ajustados para o banco novo. Conferência estática concluída; os testes funcionais foram executados depois no CAP05.
- CAP05-P01 aprovou 139 testes de backend/inicialização em bancos isolados, incluindo versão/estrutura, persistência e recusa de esquema incompatível, sem testar migração.
- CAP05-P03 criou e validou `projects_rev1.db` em caminho distinto e excluiu o legado de teste por caminho literal, com autorizações separadas. Após a validação, o banco Rev1 foi renomeado para `projects.db` e reaberto pela API com o padrão do código.

## Limites

A aplicação deve continuar recusando banco incompatível, sem migração ou reset automático. A mensagem de incompatibilidade foi atualizada para o documento vigente no CAP03-P06; não executar comandos antigos de migração.

Este documento é somente histórico e não executa operações. Os comandos de migração foram retirados para evitar que o plano anterior seja tratado como procedimento vigente. As operações de CAP05 estão registradas em [banco-novo-rev1.md](banco-novo-rev1.md); a preparação da entrega segue no CAP06-P03.
