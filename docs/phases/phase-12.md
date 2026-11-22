# Fase 12 — Controlo do computador e ferramentas

**Objectivo:** Acções no computador (apps, volume, janelas) de forma verificável e segura.

**Activa (feature flag):** computer_control

## Entregas principais
- tools/registry, tools/computer (open_app, volume, windows, close_app, confirm, platform_guard)
- tools/network (só se P-02 for confirmada; só leitura)

## Testes reais (obrigatórios no gate)
- Abrir app inexistente devolve failed, nunca done
- Injecção de comandos num nome de app não executa nada
- Fechar por nome nunca atinge o próprio assistente
- Volume lido de volta após definir
- Sem botão de confirmação, desligar não acontece
- Sem permissão do sistema: unverified ou failed com explicação

## Demonstração
'Abre o editor e baixa o volume', com o estado verificado visível.

## Gate
Bateria de segurança de ferramentas a 100%; nenhuma acção reportada como feita sem verificação.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
