MÓDULO: agents.definitions
FINALIDADE: Guardar e validar as definições de agentes do fluxo CREATE como Markdown de dados.
FUNCIONALIDADES: Cabeçalho obrigatório `id`/`nome`/`versao`/`entrada`/`saida`/`ferramentas`, rejeição de cabeçalhos inválidos, carga determinística e renderização com bloco não confiável delimitado.
ESTRUTURA:
- __init__.py — API pública.
- parser.py — leitura e validação do cabeçalho.
- prompt.py — renderização segura do texto.
- planeador.md — definição do agente de planeamento.
- arquitecto.md — definição do agente de arquitectura.
- implementador.md — definição do agente de implementação.
- revisor.md — definição do agente de revisão.
- relator.md — definição do agente de relatório.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas.
INTERFACE PÚBLICA: AgentDefinition, DefinitionError, load_agent_definitions, parse_agent_definition, render_prompt.
DEPENDÊNCIAS: internas — app.llm.egress; externas — nenhuma.
CONFIGURAÇÃO: `load_agent_definitions(caminho)`; sem argumento usa esta pasta.
UTILIZAÇÃO:
definicoes = load_agent_definitions()
prompt = render_prompt(definicoes[0], {"codigo": texto})
TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_agent_definitions.py
LIMITAÇÕES: não interpreta Markdown como código, não descarrega definições e não emite aprovações.
RELAÇÕES: será usado pelo runner do fluxo CREATE e pelo delimitador de conteúdo não confiável de `app.llm.egress`.
