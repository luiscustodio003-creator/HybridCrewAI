# Estado do projecto
Fase actual: 2 · Gate: pendente (9/13 validadas)
Última tarefa validada: HCW-02-009 (2026-11-22) — escada de modelos e matriz de fallback em `app/llm/router/ladder.py`, evidência em `docs/reports/hcw-02-009.md`.
A meio: `HCW-02-010` a `HCW-02-012` estão `APPROVED`. `HCW-00-006` continua `IMPLEMENTED` (5 erros de `ruff`, 3 de `mypy`).
Bloqueios: nenhum para `HCW-02-010`; nenhuma dependência de LLM/voz/rede foi instalada; etiquetas locais `phase-00-go` e `phase-01-go`;
 `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-02-010` — criar `app/llm/providers/` com adaptadores Gemini texto, Gemini Live e Ollama sobre `ModelRequest`/`ModelResponse`, `LiveSession` como `Protocol`, URLs base por configuração e testes com servidor HTTP falso em `tests/unit/test_providers.py`.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE.antigo.md` (fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini — já tratado como negação segura em `HCW-02-005`. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
