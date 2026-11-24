# Desenho da interface web local

Este documento descreve o cliente web servido pelo próprio servidor local. Não há recursos externos, nem dependências de rede para apresentar a página.

## Ecrãs

### Painel único

O painel é uma única página com quatro secções: tarefas, eventos, chamadas LLM e chat. O cabeçalho contém o campo de token, o botão «Ligar» e uma linha de estado. O token não é gravado em ficheiros nem no armazenamento do browser; permanece apenas em memória enquanto a página está aberta.

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

### Segurança da apresentação

Todo o conteúdo vindo do servidor é inserido como texto, nunca como marcação HTML. A política de segurança da página permite apenas recursos da mesma origem e bloqueia quadros, objectos incorporados e estilos ou scripts externos.
