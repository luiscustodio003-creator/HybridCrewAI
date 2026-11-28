# Desenho da interface web local

Este documento descreve o cliente web servido pelo próprio servidor local. Não há recursos externos, nem dependências de rede para apresentar a página.

## Ecrãs

### Painel único

O painel é uma única página com sete secções: equipa de agentes, aprovação de plano, anexos, tarefas, eventos, chamadas LLM e chat. O cabeçalho contém o campo de token, o botão «Ligar» e uma linha de estado. O token não é gravado em ficheiros nem no armazenamento do browser; permanece apenas em memória enquanto a página está aberta.

### Equipa de agentes

A secção de equipa apresenta a lista devolvida por `GET /api/agents`. Cada linha mostra `agent_id`, nome, versão, tipo de entrada e tipo de saída. O botão «Atualizar» repete a consulta; prompts e instruções completas nunca são apresentados.

### Aprovação de plano

A secção de aprovação tem os campos `task_id`, `correlation_id` e `diff_hash`, além do botão «Aprovar plano». O botão começa oculto e desactivado e só fica disponível quando o fluxo de eventos recebe `create.plano`. A submissão usa `POST /api/approvals`; o token devolvido fica apenas na variável `ultimoToken` e nunca entra no DOM. A aprovação expõe esse valor apenas à secção de anexos através de `window.hcwAprovacaoToken()`.

### Anexos

A secção de anexos tem um campo de ficheiro aceitando apenas `.zip`, os botões «Enviar para quarentena» e «Liberar anexo» e uma linha de estado. Os botões só ficam activos quando existe ficheiro e os campos de aprovação e o token estão preenchidos. O envio codifica o ZIP em base64 e usa `POST /api/attachments`; a liberação usa `POST /api/attachments/release` com o identificador devolvido. O histórico do chat é recarregado depois de cada operação e mostra a mensagem de quarentena ou o relatório de cobertura com lidos, ignorados e motivos. O conteúdo do ZIP não é apresentado na página.

### Tarefas

A secção de tarefas apresenta a lista devolvida por `GET /api/tasks`. Cada linha mostra `task_id`, estado, título, agente e fase. O botão «Atualizar» repete a consulta sem alterar dados.

### Eventos

A secção de eventos abre um fluxo em tempo real sobre `GET /api/events`. Os filtros por `correlation_id` e nível são aplicados na consulta. Cada linha mostra data/hora, nível, tipo, correlação, tarefa e mensagem. O fluxo possui botões «Iniciar fluxo» e «Parar fluxo».

### Chamadas LLM

A secção de chamadas LLM consulta `GET /api/llm-calls`, opcionalmente filtrada por `correlation_id`. Cada linha mostra data/hora, estado, fornecedor, modelo, latência, correlação e uma pré-visualização redigida do prompt.

### Chat

A secção de chat consulta `GET /api/chat` e envia mensagens por `POST /api/chat`. O envio exige `task_id` e `correlation_id`, que são enviados como dados da mensagem e não como instruções para o modelo. As respostas são apresentadas na mesma lista, com papel, identificadores e conteúdo.

## Estados

### Sem ligação

Ao abrir a página, a linha de estado indica «Por ligar». As listas ficam vazias até o utilizador introduzir o token e premir «Ligar». Nenhuma credencial é apresentada na interface.

### Ligado

Depois de «Ligar», tarefas e chamadas LLM são carregadas e o histórico do chat é apresentado. Uma falha de autenticação ou de origem é mostrada apenas como mensagem curta, sem eco do token.

### Sem plano pronto

Ao ligar, o botão «Aprovar plano» fica oculto e desactivado e a linha da aprovação indica «Sem plano pronto». Nenhum campo é enviado ao servidor neste estado.

### Plano pronto

A receção de `create.plano` torna o botão visível e activo e actualiza o estado para «Plano pronto para aprovação.». Depois de uma emissão válida, o estado passa a «Aprovação emitida.» sem apresentar o token.

### Anexo em quarentena

Sem ficheiro ou sem contexto de aprovação, os botões de anexos permanecem desactivados e o estado indica «Sem anexo». Depois de um envio válido, o estado identifica o anexo em quarentena e o chat apresenta o nome ficheiro, o digest e os identificadores da tarefa e da correlação. O anexo só é libertado depois de «Liberar anexo» com o mesmo token da aprovação; nesse momento o chat apresenta a cobertura real e o relatório passa a indicar lidos, ignorados e motivos.

### Fluxo de eventos activo

Enquanto o fluxo está activo, o botão «Iniciar fluxo» fica desactivado e o botão «Parar fluxo» fica disponível. Alterar um filtro reinicia o fluxo com o novo critério. A lista é limitada às 200 entradas mais recentes.

### Falha

Perdas de ligação, respostas inválidas e recusas do servidor actualizam a linha de estado com uma mensagem curta em português. A página continua utilizável e não repete automaticamente pedidos com credenciais inválidas.

## Interações

### Ligar ao servidor

O utilizador introduz o token e prime «Ligar». O cliente usa esse valor apenas no cabeçalho `Authorization` dos pedidos seguintes. Todas as ligações são relativas à origem da própria página.

### Actualizar listas

Os botões «Atualizar» nas secções de tarefas e chamadas LLM repetem a consulta correspondente. As alterações nos filtros de chamadas LLM disparam a consulta filtrada.

### Acompanhar eventos

O utilizador escolhe correlação e nível, prime «Iniciar fluxo» e vê os eventos à medida que chegam. «Parar fluxo» cancela a ligação sem fechar a página.

### Enviar mensagem

O utilizador preenche `task_id`, `correlation_id` e mensagem, depois submete o formulário. O cliente envia um objecto JSON com três campos e recarrega o histórico. A mensagem não é enviada se algum campo estiver vazio.

### Listar equipa

Depois de «Ligar», a equipa é carregada automaticamente. O botão «Atualizar» repete a consulta sem alterar o servidor nem expor prompts.

### Aprovar plano

O utilizador preenche `task_id`, `correlation_id` e `diff_hash`, confirma que o botão ficou visível após `create.plano` e prime «Aprovar plano». O cliente envia apenas esses três campos e guarda o token devolvido em `ultimoToken`, sem o copiar para a página nem para o armazenamento local.

### Enviar e libertar anexo

O utilizador escolhe um ZIP e prime «Enviar para quarentena». O cliente lê o ficheiro com `FileReader`, envia os dados em base64 e guarda apenas o identificador devolvido. Depois de confirmar o relatório de quarentena no chat, prime «Liberar anexo». O cliente envia o identificador, os identificadores de aprovação e o token em memória, e recarrega o chat; a linha de estado passa a apresentar a cobertura devolvida. Nenhum destino aceita ficheiros por arrastar e nenhum pedido sai da origem local.

### Segurança da apresentação

Todo o conteúdo vindo do servidor é inserido como texto, nunca como marcação HTML. A política de segurança da página permite apenas recursos da mesma origem e bloqueia quadros, objectos incorporados e estilos ou scripts externos.
