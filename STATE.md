# Estado do projecto
Fase actual: 2 · Gate: pendente (3/13 validadas)
Última tarefa validada: HCW-02-003 (2026-11-22) — contratos base do gateway em `app/llm/contracts.py`, evidência em `docs/reports/hcw-02-003.md`.
A meio: `HCW-02-004` está `APPROVED`; `HCW-02-005` a `HCW-02-012` também estão `APPROVED`. `HCW-00-006` continua `IMPLEMENTED` (5 erros de `ruff`, 3 de `mypy`).
Bloqueios: nenhum para `HCW-02-004`; nenhuma dependência de LLM/voz/rede foi instalada; etiquetas locais `phase-00-go` e `phase-01-go`; `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-02-004` — criar `app/llm/egress/` com varredura de segredos no payload, política `CloudDenied` por omissão e embrulho de conteúdo não confiável, mais `tests/security/test_egress.py` e documentação do módulo. Não instalar dependências.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE.antigo.md` (fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
