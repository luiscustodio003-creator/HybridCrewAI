# Estado do projecto
Fase actual: 2 · Gate: pendente (2/13 validadas)
Última tarefa validada: HCW-02-002 (2026-11-22) — ADR-0002 aprovado e registado em `docs/adr/ADR-0002-gateway-de-modelos.md`.
A meio: `HCW-02-003` está `APPROVED`; `HCW-02-004` a `HCW-02-012` também estão `APPROVED`. `HCW-00-006` continua `IMPLEMENTED` (5 erros de `ruff`, 3 de `mypy`).
Bloqueios: nenhum para `HCW-02-003`; ADR-0002 está `ACEITE`; nenhuma dependência de LLM/voz/rede foi instalada; etiquetas locais `phase-00-go` e `phase-01-go`; `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-02-003` — criar `app/llm/contracts.py` com `ModelRequest`, `ModelResponse` e `ProviderError` imutáveis, timeout positivo obrigatório e `repr` sem segredos, mais testes em `tests/unit/test_llm_contracts.py` e `README.txt`/`module.yaml` da pasta `app/llm`. Não instalar dependências.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
