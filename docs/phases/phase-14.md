# Fase 14 — Avaliação contínua, documentação e distribuição

**Objectivo:** Fechar o produto.

**Activa (feature flag):** avaliação, documentação automática, distribuição

## Entregas principais
- harness de avaliação com 20+ casos e comparador de modelos/prompts
- documentação automática MD/HTML com diagramas determinísticos
- instalador, actualizações, migração de dados, desinstalação, manual

## Testes reais (obrigatórios no gate)
- Instalação limpa em máquina nova, Windows e Linux
- Actualização com migração e recuperação se falhar
- Desinstalação sem resíduos
- Comparar dois modelos nos casos de referência e detectar regressão de prompt

## Demonstração
Instalar do zero, criar, analisar e melhorar um projecto por texto e por voz.

## Gate
Instalação limpa e todos os gates anteriores verdes.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
