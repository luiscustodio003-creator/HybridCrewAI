---
name: hcw-docs
description: Documenta o HybridCrewAI em português de Portugal com modelos fixos. Usar quando for preciso escrever ou actualizar README.txt de módulo, module.yaml, ADR, relatório de fase, entrada de DEVLOG, docs/MAP.md ou qualquer documentação, e no fim de cada tarefa e de cada fase. Garante que a documentação nunca fica para trás do código.
---

# Documentação

Documentar não é uma fase final: é parte de cada tarefa. Uma tarefa sem documentação não está `IMPLEMENTED`.

## Por tarefa
- Cada pasta de módulo com código: `README.txt` (modelo `templates/README_TEMPLATE.txt`) e `module.yaml` (modelo `templates/MODULE_TEMPLATE.yaml`). Verificado por `python scripts/check_modules.py`.
- Docstrings em PT-PT nas interfaces públicas; comentários só onde o porquê não é óbvio.
- Entrada no `DEVLOG.md`.

## Por decisão
- Qualquer escolha de tecnologia ou arquitectura: `docs/adr/ADR-NNNN-titulo.md` pelo modelo `templates/ADR_TEMPLATE.md`. Estado inicial `PROPOSTA`; só o utilizador a passa a `ACEITE`.

## Por fase
- `docs/reports/phase-NN.md` (modelo `templates/PHASE_REPORT_TEMPLATE.md`): o que foi feito, testes, evidências, limitações, decisões, ideias adiadas.
- Actualizar `docs/MAP.md` («onde está o quê»: responsabilidade, pasta, ficheiro principal).

## Regras
- Português de Portugal, tom directo, sem floreados; termos técnicos em inglês quando são o nome oficial.
- Nunca descrever funcionalidades que não existem: distinguir «implementado», «validado» e «proposto».
- Nada de segredos nem caminhos pessoais na documentação.
