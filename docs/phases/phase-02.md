# Fase 02 — LLM Gateway com política de egress

**Objectivo:** Uma única porta para os modelos, com controlo do que sai para a cloud. Gemini Live para conversa, modelos de texto Gemini para agentes, Ollama em segundo plano.

**Activa (feature flag):** gateway

## Entregas principais
- llm/contracts, providers (gemini_live, gemini_text, ollama)
- router (ladder, cooldown, errors), budget (tokens, tools_budget)
- egress (secret_scan, policy, untrusted_wrap)
- prompts versionados em ficheiros .md
- ADR-0002 (LiteLLM vs SDK nativo; LiveSession atrás de contrato)

## Testes reais (obrigatórios no gate)
- Ollama real e Gemini real (opcional) devolvem resposta válida
- Timeout, 429 e resposta inválida: classificação, retries limitados, cooldown por tipo de erro
- Teste que falha se alguma chamada não tiver timeout
- Matriz de fallback: Gemini para Gemini automático; outro cloud só com autorização; Ollama só tarefas leves
- Egress: servidor falso capta o pedido e a chave falsa não aparece
- Primeiro arranque pede consentimento cloud único
- Prompt injection tratado como dados delimitados

## Demonstração
hcw llm ping mostra fornecedor, latência e o que seria enviado, já redigido.

## Gate
Matriz de fallback completa; zero segredos no payload; quotas e orçamento a funcionar.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
