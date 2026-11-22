# HybridCrewAI — instruções para o agente (OpenCode, Codex)

Projecto: assistente pessoal estilo JARVIS com equipa de agentes de engenharia de software. Idioma: documentação, comentários e interface em português de Portugal; identificadores e nomes de ficheiros em inglês.

## Como trabalhar aqui
1. **Antes de qualquer acção**, carregar a Skill `hcw-router` (pasta `.opencode/skills/`). Ela manda ler `STATE.md` e correr `python scripts/plan_status.py`.
2. Para avançar no projecto, usar a Skill `hcw-phase-runner`.
3. Terminar sempre cada sessão com a Skill `hcw-handoff`.

## Regras que nunca mudam
- Uma tarefa de cada vez, só as que estão `APPROVED` em `tasks.yaml`. O utilizador aprova planos, ADR e operações destrutivas.
- Ficheiros com no máximo 300 linhas; um README.txt e um module.yaml por módulo.
- Nunca marcar `VALIDATED` sem evidência real (testes executados, relatório em `reports/`).
- O modelo propõe, o Python executa: nunca executar texto de um modelo como comando.
- Nunca guardar segredos em ficheiros, logs ou no Git.
- Não inventar APIs nem bibliotecas; confirmar versões na documentação oficial.
- Ideias novas vão para `IDEAS.md` (Skill `hcw-ideas-intake`), não para o código.

## Ficheiros de controlo
`tasks.yaml` (estado do plano) · `STATE.md` · `DEVLOG.md` · `IDEAS.md` · `THREAT_MODEL.md` · `docs/phases/` · `docs/requirements.yaml` · `scripts/`
