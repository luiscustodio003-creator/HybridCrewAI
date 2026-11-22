# Estado do projecto
Fase actual: 2 · Gate: pendente (4/13 validadas)
Última tarefa validada: HCW-02-004 (2026-11-22) — egress e redacção em `app/llm/egress/`, evidência em `docs/reports/hcw-02-004.md`.
A meio: `HCW-02-005` está `APPROVED`; `HCW-02-006` a `HCW-02-012` também estão `APPROVED`. `HCW-00-006` continua `IMPLEMENTED` (5 erros de `ruff`, 3 de `mypy`).
Bloqueios: nenhum para `HCW-02-005`; nenhuma dependência de LLM/voz/rede foi instalada; etiquetas locais `phase-00-go` e `phase-01-go`;
 `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-02-005` — criar `app/llm/consent.py` com consentimento cloud explícito e tipo de conta Gemini, recusando `desconhecido`/ausente; adicionar `tests/unit/test_llm_consent.py`; atualizar `app/core/config/defaults.py` sem ler nem gravar segredos. Não instalar dependências.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE.antigo.md` (fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini — a HCW-02-005 deve tratar `desconhecido` como negação até o utilizador decidir. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
