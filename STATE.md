# Estado do projecto
Fase actual: 2 · Gate: pendente (1/13 validadas)
Última tarefa validada: HCW-02-001 (2026-11-22) — plano da Fase 2 aprovado e registado em `docs/reports/phase-02-plan.md`.
A meio: `HCW-02-002` está `APPROVED`; `HCW-02-003` a `HCW-02-012` também ficaram `APPROVED` após aprovação do plano. `HCW-00-006` continua `IMPLEMENTED` (5 erros de `ruff`, 3 de `mypy`).
Bloqueios: nenhum para a Fase 2; etiquetas locais `phase-00-go` e `phase-01-go`; um commit de planeamento da Fase 2 sem push para `origin/master`; `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-02-002` — escrever `docs/adr/ADR-0002-gateway-de-modelos.md` com estado `PROPOSTA`, correr `python scripts/validate_plan.py` e parar para o utilizador aprovar o ADR antes de `HCW-02-003`. Não instalar `httpx`, `google-genai`, `litellm` nem `ollama` sem aprovação.
Decisões pendentes: aprovação de ADR-0002; validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
