# Fase 11 — Voz JARVIS (Gemini Live)

**Objectivo:** Falar com o assistente e ouvi-lo em PT-PT, assente no Gemini Live, com modo offline opcional.

**Activa (feature flag):** voice

## Entregas principais
- voice (live, stt, tts, session, commands, interrupt, devices, push_to_talk, echo_guard, wake_word opcional)
- ecrã Voz

## Testes reais (obrigatórios no gate)
- Áudios gravados em PT-PT com taxa de acerto mínima
- Latência de ponta a ponta medida
- Interrupção por voz corta a síntese e ajusta a tarefa
- Guarda contra eco
- Teste de microfone e escolha de dispositivos
- Ligação interrompida não apaga a conversa
- Sem rede: avisa e passa a texto ou voz local

## Demonstração
Pedir uma tarefa por voz, interromper e receber o progresso falado.

## Gate
Metas de acerto e latência cumpridas; modo texto equivalente.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
