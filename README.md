# HybridCrewAI — pacote de Skills e controlo para o OpenCode

Faz o OpenCode construir o projecto **fase a fase, documentando e validando cada passo**, sem perder o contexto entre sessões.

## O que vem no pacote
| Pasta/ficheiro | Para quê |
|---|---|
| `.opencode/skills/` | 10 Skills (router, phase-runner, handoff, ideas-intake, audit, plan, implement, test-gate, security-review, docs) |
| `AGENTS.md` | Regras curtas que o OpenCode lê sempre |
| `tasks.yaml` | Estado do plano: 15 fases, 48 tarefas (Fases 0 e 1 detalhadas; as outras detalham-se quando chegam) |
| `docs/phases/` | Ficha de cada fase (entregas, testes reais, demonstração, gate) |
| `docs/requirements.yaml` | Requisitos com identificadores (FR, NFR, SEC, OPS, DOC) |
| `STATE.md`, `DEVLOG.md`, `IDEAS.md`, `THREAT_MODEL.md` | Continuidade, diário, caixa de ideias e modelo de ameaças |
| `scripts/` | Guardas reais: `validate_plan`, `check_file_size`, `check_modules`, `lint_skills`, `check_traceability`, `plan_status`, `run_gate` |
| `tests/scripts/` | Testes dos próprios scripts |

## Instalação (5 minutos)
1. Copie **todo o conteúdo** desta pasta para a raiz do projecto HybridCrewAI (mantendo `.opencode/`).
2. Com o ambiente virtual activo: `pip install pyyaml pytest`.
3. Verifique: `python scripts/lint_skills.py` e `python -m pytest -q tests/scripts` (devem passar).
4. Abra o OpenCode na raiz do projecto. Se as Skills não aparecerem, confirme que o ficheiro se chama `SKILL.md` em maiúsculas e reinicie o OpenCode.

## Primeira mensagem para o OpenCode
> Carrega a Skill `hcw-router`, lê o `STATE.md` e corre `python scripts/plan_status.py`. Depois usa a Skill `hcw-phase-runner` para continuar a Fase 0. Pára sempre que for preciso eu aprovar algo.

## Como funciona o ciclo
`situar` → `planear (tu aprovas)` → `implementar tarefa` → `rever segurança` → `testar` → `documentar` → `commit` → ... → `gate da fase (GO/NO-GO)` → `etiqueta phase-NN-go` → `handoff`.

Comandos úteis: `python scripts/plan_status.py` · `python scripts/validate_plan.py` · `python scripts/run_gate.py --phase 0`.

## Limites (honestidade)
- Os scripts e os testes foram executados no meu ambiente; o `pytest` não estava disponível lá, por isso os 18 testes foram corridos com um executor mínimo. **Corra-os com o pytest real no seu ambiente.**
- A tarefa `HCW-00-006` está `IMPLEMENTED`, não `VALIDATED`: só passa a validada com evidência no seu ambiente.
- Os gates das Fases 2 em diante pedem testes reais (Ollama, Gemini, Playwright, Docker) que dependem do seu hardware e contas.
- Confirmei na documentação do OpenCode que lê Skills em `.opencode/skills/<nome>/SKILL.md` (e em `.claude/skills/`), com o nome igual ao da pasta.
