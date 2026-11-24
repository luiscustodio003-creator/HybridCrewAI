MÓDULO: ui/web
FINALIDADE: Servir o cliente web local, estático e sem recursos externos para tarefas, eventos, chamadas LLM e chat.
FUNCIONALIDADES: página única em index.html; folha de estilo local; consulta de tarefas e chamadas LLM; fluxo de eventos com filtros por correlation_id e nível; histórico e envio de mensagens no chat; token mantido apenas em memória; conteúdo do servidor inserido como texto; ausência de ligações externas.
ESTRUTURA: index.html (marcação da página); styles.css (apresentação local); tasks.js (ligação, cliente JSON e tarefas); logs.js (fluxo SSE por fetch com cancelamento); llm_calls.js (consulta filtrada de chamadas LLM); chat.js (histórico e envio de mensagens); DESIGN.md (ecrãs, estados e interações).
INTERFACE PÚBLICA: nenhuma API Python; os recursos são servidos pelo módulo ui/server nas rotas /, /index.html, /styles.css, /tasks.js, /logs.js, /llm_calls.js e /chat.js.
DEPENDÊNCIAS: ui/server; API do browser para fetch, AbortController, TextDecoder e URLSearchParams; biblioteca padrão do browser.
CONFIGURAÇÃO: o utilizador introduz o token no cabeçalho da página; o cliente usa apenas caminhos relativos e não grava credenciais.
UTILIZAÇÃO: abrir a raiz do servidor local, introduzir o token e premir «Ligar»; usar os botões de atualização e filtros conforme o desenho em DESIGN.md.
TESTES: python -m pytest -q tests/unit/test_ui_web_assets.py
LIMITAÇÕES: o cliente não possui autenticação própria e depende do token introduzido pelo utilizador; o fluxo de eventos usa fetch em fluxo e requer browser com ReadableStream; as credenciais não sobrevivem a recarregar a página.
RELAÇÕES: complementa ui/server e consome as rotas já protegidas por Bearer token e validação de origem da Fase 3.
