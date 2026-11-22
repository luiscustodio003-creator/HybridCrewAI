# Fase 06 — Execução isolada

**Objectivo:** Substituir o executor mínimo por isolamento a sério.

**Activa (feature flag):** sandbox_exec

## Entregas principais
- execution/executors (contract, docker, venv), limits, capture, cleanup
- ADR-0003 (Docker, WSL, venv restrito, Windows Sandbox Pro/Enterprise)

## Testes reais (obrigatórios no gate)
- Ler fora da pasta, abrir rede ou ler credenciais falha
- Ciclo infinito termina no timeout; memória excessiva cortada
- stdout/stderr capturados
- Sem processos ou contentores órfãos
- Scripts de ZIP nunca correm automaticamente
- Sem mecanismo seguro: o sistema recusa e explica

## Demonstração
Correr um programa malicioso de teste e ver cada fuga bloqueada e registada.

## Gate
Testes de fuga todos bloqueados; sem processos órfãos.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
