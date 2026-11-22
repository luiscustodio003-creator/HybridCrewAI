# Fase 00 — Fundação, auditoria e escolha do motor

**Objectivo:** Conhecer o estado real do código, montar a linha de montagem de qualidade e decidir o motor de agentes com evidência.

**Activa (feature flag):** guardas de CI e validação do plano

## Entregas principais
- pyproject.toml, CI (Windows e Linux), pre-commit
- scripts/ de guarda (já fornecidos no pacote)
- relatório de auditoria, baseline, spike e ADR-0001
- Git com etiquetas por fase

## Testes reais (obrigatórios no gate)
- Suite existente executada e baseline guardada (referência histórica: 197 testes)
- check_file_size falha num ficheiro de 301 linhas
- Instalação limpa em venv novo, Windows e Linux
- Spike: mesmo cenário (pedido, plano, pausa, matar processo, retoma) em núcleo próprio, CrewAI e LangGraph

## Demonstração
Abrir o relatório de auditoria e a tabela do spike.

## Gate
Baseline guardada; CI verde nos dois sistemas; ADR-0001 aprovado pelo utilizador.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
