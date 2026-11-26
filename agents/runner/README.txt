MÓDULO: agents.runner
FINALIDADE: Executar definições locais de agentes de forma determinística, devolvendo ToolResult verificável.
FUNCIONALIDADES: Prompt renderizado com bloco não confiável delimitado, saída JSON validada, no máximo duas repetições, eventos com rastreabilidade e aprovação reivindicada pelo modelo sem efeito.
ESTRUTURA:
- __init__.py — API pública.
- models.py — AgentRun, RunnerConfig, AgentOutput e validação da saída.
- loader.py — carga e selecção das definições locais.
- engine.py — AgentRunner e publicação de eventos.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas.
INTERFACE PÚBLICA: AgentOutput, AgentRun, AgentRunError, AgentRunner, ApprovalState, DefinitionNotFoundError, ForgedMarkerError, OutputValidationError, RunnerConfig, load_runner_definitions, parse_agent_output.
DEPENDÊNCIAS: internas — agents.definitions, app.core.events, app.core.results, app.llm.contracts, app.llm.egress; externas — nenhuma.
CONFIGURAÇÃO: RunnerConfig(provider_kind, model, timeout_s, max_retries=2).
UTILIZAÇÃO:
runner = AgentRunner(provider, RunnerConfig(ProviderKind.FAKE, "fake-model", 5))
resultado = runner.executar(AgentRun("planeador", "t1", "c1", "create"))
TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_agent_runner.py
LIMITAÇÕES: Não inicia rede, subprocesso ou modelo por omissão; não emite tokens de aprovação; não executa comandos nem código proposto pelo modelo.
RELAÇÕES: usa `agents.definitions` e será usado por `workflows/create` e pelo painel de aprovação.
