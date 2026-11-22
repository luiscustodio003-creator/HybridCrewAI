# Estado do projecto
Fase actual: 2 · Gate: pendente (0/13 validadas)
Última tarefa validada: HCW-01-999 (2026-11-22) — gate da Fase 1 em `reports/phase-01/report.md`.
A meio: HCW-02-001 (plano detalhado criado em `tasks.yaml`; tarefas `HCW-02-002` a `HCW-02-012` em `PLANNED`; aguarda aprovação). `HCW-00-006` continua `IMPLEMENTED` (5 erros de `ruff`, 3 de `mypy`).
Bloqueios: nenhum para o planeamento; quinze commits locais sem push para `origin/master`; etiquetas locais `phase-00-go` e `phase-01-go`; `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: obter aprovação do utilizador para o plano (`HCW-02-001`) e para ADR-0002; só depois passar as tarefas aprovadas a `APPROVED` e iniciar `HCW-02-002`. Não instalar `httpx`, `google-genai`, `litellm` nem `ollama` sem aprovação.
Decisões pendentes: aprovação do plano da Fase 2; ADR-0002 (LiteLLM vs SDK nativo); validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
