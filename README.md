# Monitoramento de Projetos em Workflow

MVP para acompanhar projetos ao longo de um workflow, reunindo em um só lugar seus dados, etapas e andamento. A proposta é oferecer uma base simples para visualizar o estado dos projetos e facilitar sua evolução entre etapas.

> **Status:** estrutura inicial do projeto. O endpoint `GET /health` está disponível; as demais funcionalidades descritas como objetivo e roadmap ainda serão implementadas.

## Objetivo

Construir uma aplicação web leve para cadastrar projetos, acompanhar sua situação no workflow e consultar informações relevantes para sua gestão. O MVP prioriza uma interface direta, uma API em Python e persistência local com SQLite.

## Stack

- **Back-end:** Python e FastAPI
- **Persistência:** SQLite
- **Front-end:** HTML, Bootstrap e JavaScript
- **Servidor de desenvolvimento:** Uvicorn

## Arquitetura proposta

O navegador apresenta as telas em HTML, com componentes de interface estilizados pelo Bootstrap e interações implementadas em JavaScript. O JavaScript se comunica com a API HTTP do FastAPI, que concentra as regras da aplicação e acessa o SQLite para persistir os dados.

```text
Navegador
  └── HTML + Bootstrap + JavaScript
        └── API HTTP (FastAPI)
              └── Regras da aplicação
                    └── SQLite
```

Essa organização separa apresentação, API e persistência sem exigir serviços externos para executar o MVP localmente.

## Pré-requisitos

- Python 3.11 ou superior
- `pip`
- Git (opcional, para obter o código por clone)

## Execução local

O repositório está no início do desenvolvimento e ainda não contém um manifesto de dependências. Os passos abaixo permitem iniciar a aplicação FastAPI atual, disponível em `app/main.py`.

1. Crie e ative um ambiente virtual na raiz do projeto:

   **Windows (PowerShell):**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **Linux ou macOS:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Instale as dependências básicas previstas:

   ```bash
   python -m pip install fastapi uvicorn
   ```

3. Inicie o servidor na raiz do projeto:

   ```bash
   uvicorn app.main:app --reload
   ```

4. Acesse `http://127.0.0.1:8000/health` para consultar o estado da aplicação. A documentação interativa da API fica disponível em `http://127.0.0.1:8000/docs`.

> A instalação acima é apenas o mínimo para iniciar o servidor FastAPI. Dependências de acesso ao banco, configuração e execução completa serão registradas em um arquivo de dependências quando a aplicação for implementada.

## Roadmap

- [ ] Definir os dados de projeto e as etapas do workflow.
- [ ] Implementar a API FastAPI e a persistência SQLite.
- [ ] Criar operações para cadastrar, consultar, atualizar e remover projetos.
- [ ] Construir a interface para listar projetos e visualizar seu andamento.
- [ ] Adicionar filtros e movimentação de projetos entre etapas.
- [ ] Registrar dependências e instruções definitivas de instalação.
- [ ] Adicionar testes automatizados e orientações para execução em produção.

## Contribuição

Durante o desenvolvimento, crie uma branch para sua alteração, mantenha as mudanças focadas e descreva no pull request o que foi alterado e como foi verificado. Instruções específicas de contribuição e testes serão adicionadas conforme a estrutura da aplicação evoluir.
