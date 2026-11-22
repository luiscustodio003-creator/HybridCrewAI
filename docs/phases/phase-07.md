# Fase 07 — Project Intelligence e painel de análise de código

**Objectivo:** Compreender projectos existentes sem enviar tudo ao LLM.

**Activa (feature flag):** analysis

## Entregas principais
- analysis/scanners (linguagem, entrypoints, dependências, duplicados, não usados)
- analysis/graph e quality (Ruff, mypy, Bandit, pip-audit)
- context_selector com orçamento de tokens; verificação de citações; ecrã Análise de código

## Testes reais (obrigatórios no gate)
- Analisar o próprio HybridCrewAI e comparar com MAP.md
- Fixtures com defeitos plantados (ciclo de imports, duplicação, segredo, dependência vulnerável) todos encontrados
- Comentários com prompt injection não alteram o agente
- Citação inventada detectada

## Demonstração
Analisar um projecto no chat e navegar pelo grafo e pelos achados.

## Gate
Defeitos plantados detectados; relatório técnico gerado.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
