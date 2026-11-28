(function () {
  "use strict";

  const api = window.hcwApi;
  const lista = document.getElementById("mensagens");
  const campo = document.getElementById("chat-mensagem");

  function tarefa() {
    return document.getElementById("chat-tarefa").value.trim();
  }

  function correlacao() {
    return document.getElementById("chat-correlacao").value.trim();
  }

  function caminho() {
    const valor = tarefa();
    return valor ? "/api/chat?task_id=" + encodeURIComponent(valor) : "/api/chat";
  }

  function mostrar(dados) {
    lista.replaceChildren();
    if (!Array.isArray(dados) || dados.length === 0) {
      api.item(lista, "Sem mensagens registadas.");
      return;
    }
    for (const mensagem of dados) {
      const li = document.createElement("li");
      li.textContent = [
        mensagem.created_at,
        mensagem.role,
        mensagem.task_id,
        mensagem.correlation_id,
        mensagem.content,
      ]
        .filter(Boolean)
        .join(" · ");
      lista.appendChild(li);
    }
  }

  async function carregar() {
    try {
      mostrar(await api.getJson(caminho()));
    } catch (erro) {
      api.aviso(erro.message);
    }
  }

  async function enviar(evento) {
    evento.preventDefault();
    const mensagem = campo.value.trim();
    if (!document.getElementById("token").value.trim()) {
      api.aviso("Introduza o token da interface.");
      return;
    }
    if (!mensagem || !tarefa() || !correlacao()) {
      api.aviso("Preencha mensagem, task_id e correlation_id.");
      return;
    }
    try {
      await api.postJson("/api/chat", {
        message: mensagem,
        task_id: tarefa(),
        correlation_id: correlacao(),
      });
      campo.value = "";
      await carregar();
      api.aviso("Mensagem enviada.");
    } catch (erro) {
      api.aviso(erro.message);
    }
  }

  window.hcwChatRecarregar = carregar;

  api.registar(carregar);
  document.getElementById("formulario-chat").addEventListener("submit", enviar);
})();
