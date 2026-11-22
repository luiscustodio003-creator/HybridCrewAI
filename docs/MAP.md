# Mapa do projecto — Fase 0

Data: 2026-11-22 · Responsabilidade: DOC-001 · Estado: relatório final da auditoria da Fase 0

Este ficheiro responde a «onde está o quê». Distingue o que existe em disco do que apenas está previsto no plano. O conteúdo dos ficheiros listados é a fonte de verdade; este mapa é um índice, não substitui os relatórios de evidência.

## Estado real

- Raiz do projecto sem pasta `app/`: a Fase 0 criou apenas infra-estrutura de controlo, documentação, guardas e CI.
- Plano com 12 tarefas na Fase 0; 9 passam a estar `VALIDATED` com `HCW-00-011`, incluindo o mapa final.
- Repositório Git com `origin/master` e etiqueta `phase-00-start` no commit inicial `fd9ac9c`.
- Ambiente controlado: `.venv` com Python 3.12.0; Python global 3.15.2 fora do projecto.
- CI verde em `ubuntu-latest` e `windows-latest`; evidência em `docs/reports/hcw-00-008.txt`.
- ADR-0001 aprovado: núcleo próprio, com adaptadores futuros para CrewAI e LangGraph.

## Responsabilidades existentes

| Responsabilidade | Pasta | Ficheiro principal | Estado |
|---|---|---|---|
| Regras globais do agente | raiz | `AGENTS.md` | existente |
| Apresentação e instalação | raiz | `README.md` | existente |
| Plano mestre e estados | raiz | `tasks.yaml` | validado por guardas |
| Continuidade da sessão | raiz | `STATE.md`, `DEVLOG.md` | existente e actualizado |
| Ideias fora do plano | raiz | `IDEAS.md` | existente |
| Modelo de ameaças | raiz | `THREAT_MODEL.md` | existente |
| Guarda de plano | `scripts/` | `validate_plan.py` | 18 testes no conjunto de scripts |
| Guarda de rastreabilidade | `scripts/` | `check_traceability.py` | sem teste directo; corrido nos gates |
| Guarda de tamanho de ficheiro | `scripts/` | `check_file_size.py` | testado |
| Guarda de módulos | `scripts/` | `check_modules.py` | testado; aviso por `app/` ainda não existir |
| Validação das Skills | `scripts/` | `lint_skills.py` | testado |
| Estado e próxima tarefa | `scripts/` | `plan_status.py` | corrido em cada handoff |
| Orquestração do gate | `scripts/` | `run_gate.py` | a usar no `HCW-00-999` |
| Auxiliar partilhado | `scripts/` | `_common.py` | testado indirectamente |
| Testes dos guardas | `tests/scripts/` | `test_*.py` | 18 passaram no `.venv` |
| Fichas das fases | `docs/phases/` | `phase-00.md` a `phase-14.md` | existentes |
| Requisitos | `docs/` | `requirements.yaml` | existente |
| Decisão do motor | `docs/adr/` | `ADR-0001-motor-de-agentes.md` | ACEITE |
| Auditoria inicial | `docs/reports/` | `audit.md` | VALIDADA em HCW-00-001 |
| Baseline de ambiente | `docs/reports/` | `baseline-freeze.txt` | VALIDADA em HCW-00-001 |
| Baseline de testes | `docs/reports/` | `baseline-tests.txt` | histórico: sem testes iniciais |
| Spike do motor | `docs/reports/` | `spike-agent-engine.md` | VALIDADO em HCW-00-009 |
| Evidências por tarefa | `docs/reports/` | `hcw-00-003.txt` a `hcw-00-008.txt` | existentes |
| Mapa do código | `docs/` | `MAP.md` | este ficheiro |
| Plano de origem | `docs/` | `HybridCrewAI — Relatório Completo do Projecto e Plano Mestre v3.md` | referência histórica, não instrução |
| Skills do projecto | `.opencode/skills/` | `hcw-*/SKILL.md` | 10 Skills validadas pelo lint |
| CI | `.github/workflows/` | `ci.yml` | VALIDADA em HCW-00-008 |
| Hooks locais | raiz | `.pre-commit-config.yaml` | VALIDADOS em HCW-00-007 |
| Configuração de ferramentas | raiz | `pyproject.toml` | validada em HCW-00-004 |
| Dependências fixadas | raiz | `requirements.lock.txt` | 25 pacotes |
| Ambiente virtual | `.venv/` | `pyvenv.cfg` | ignorado pelo Git |
| Configuração do editor | `.vscode/` | `settings.json` | aponta para o `.venv` |

## Ficheiro legado fora do Git

`STATE .md` (com espaço antes da extensão) é uma cópia antiga e não deve ser usada. A fonte activa é `STATE.md`, sem espaço. A renomeação/remoção do ficheiro legado exige decisão do utilizador.

## Estrutura prevista — ainda não existe

A árvore abaixo é a meta do plano; as pastas só devem ser criadas quando a fase correspondente as exigir.

| Responsabilidade futura | Pasta prevista | Fase |
|---|---|---|
| Configuração, eventos, tarefas, logs e resultados | `app/core/` | 1 |
| Fornecedores LLM, encaminhamento, egress e orçamento | `app/llm/` | 2 |
| Servidor e interface web | `app/ui/`, `app/ui/web/` | 3 |
| Fluxo CREATE ponta a ponta | `app/workflows/create/` | 4 |
| Workspace, ZIP, snapshots e auditoria | `app/workspace/` | 5 |
| Execução isolada | `app/execution/` | 6 |
| Análise de código e grafo | `app/analysis/` | 7 |
| Conhecimento | `app/knowledge/` | 10 |
| Voz e Gemini Live | `app/voice/` | 11 |
| Ferramentas de computador, rede e engenharia reversa | `app/tools/` | 12 e 13 |
| Autonomia, rotinas e checkpoints | `app/autonomy/` | 9 |
| Aprovações por token e diff | `app/approvals/` | 4 e 12 |
| CLI de utilizador | `app/cli/` | 14 |
| Dados locais e relatórios gerados | `config/`, `data/`, `projects/`, `reports/`, `logs/` | conforme necessário |
| Testes por natureza | `tests/unit/`, `integration/`, `contracts/`, `security/`, `recovery/`, `ui/`, `eval/`, `fixtures/` | fases seguintes |

## Fecho da auditoria da Fase 0

- Entregas verificadas: baseline, 18 testes de guardas, CI em dois sistemas, pre-commit, Git com tag inicial, spike documental e ADR-0001.
- Ameaça tratada: `Dependência ou ferramenta comprometida` — versões fixadas e CI com acções oficiais; evidência em `docs/reports/hcw-00-008.txt`.
- Ameaça tratada: `Acção reportada como feita sem o ter sido` — evidências por saída real e códigos de saída nos relatórios de tarefa.
- Limitação aberta: `HCW-00-006` permanece `IMPLEMENTED`; `ruff` e `mypy` têm erros pré-existentes fora do âmbito desta tarefa.
- Limitação aberta: não existe aplicação, servidor nem funcionalidade de utilizador; o núcleo começa na Fase 1.
- Segredo: nenhuma credencial foi encontrada nos inventários de auditoria; nenhuma foi acrescentada nesta tarefa.

## Como usar este mapa

1. Para estado do plano, abrir `STATE.md` e correr `python scripts/plan_status.py`.
2. Para decisões de arquitectura, abrir `docs/adr/ADR-0001-motor-de-agentes.md`.
3. Para evidência de CI, abrir `docs/reports/hcw-00-008.txt`.
4. Para o ponto de partida, abrir `docs/reports/audit.md`.
