# Fase 05 — Workspace seguro, ZIP, Chat com anexos, diff e snapshots

**Objectivo:** Dar poder de escrita sem perder o controlo. Primeiro a segurança, depois a capacidade.

**Activa (feature flag):** workspace_write, snapshots, diff, ZIP, Permissões, anexos no Chat

## Entregas principais
- workspace (paths, symlinks, scanner, sensitive, archive, snapshot, rollback, audit, file_ops)
- approvals/diff; ui/web/attachments.js
- ecrãs Aprovações e diff, Snapshots, Permissões

## Testes reais (obrigatórios no gate)
- Path traversal, caminhos absolutos, nomes reservados do Windows, caminhos longos
- Symlink exterior bloqueado
- ZIP: Zip Slip, ZIP bomb, symlinks, ZIP dentro de ZIP além do limite
- Cobertura do chat: lidos + ignorados bate com o disco, com motivo para cada ignorado
- Anexos em quarentena até aprovação
- Snapshot, alterar, rollback devolve hashes idênticos; Undo
- Interrupção a meio de operação deixa a pasta consistente

## Demonstração
Largar um ZIP com subpastas no chat, ver o relatório de cobertura, aprovar e desfazer.

## Gate
Bateria de segurança a 100%; rollback comprovado; nenhuma escrita fora do workspace.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
