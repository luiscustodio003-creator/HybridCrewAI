(function () {
  "use strict";

  const api = window.hcwApi;
  const lista = document.getElementById("llm");
  let pedidoAtual = 0;

  function executar() {
    const pedido = ++pedidoAtual;
    const correlacao = document.getElementById("llm-correlacao").value.trim();
    const caminho = correlacao
      ? "/api/llm-calls?correlation_id=" + encodeURIComponent(correlacao)
      : "/api/llm-calls";
    api.getJson(caminho)
      .then(function (dados) {
        if (pedido === pedidoAtual) mostrar(dados);
      })
      .catch(function (erro) {
        if (pedido === pedidoAtual) api.aviso(erro.message);
      });
  }

  function mostrar(dados) {
    lista.replaceChildren();
    if (!Array.isArray(dados) || dados.length === 0) {
      api.item(lista, "Sem chamadas LLM registadas.");
      return;
    }
    for (const chamada of dados) {
      const li = document.createElement("li");
      li.textContent = [
        chamada.timestamp,
        chamada.status,
        chamada.provider,
        chamada.model,
        chamada.latency_ms + " ms",
        chamada.correlation_id,
        chamada.prompt_preview,
      ]
        .filter(function (valor) {
          return valor !== null && valor !== undefined && valor !== "";
        })
        .join(" · ");
      lista.appendChild(li);
    }
  }

  api.registar(executar);
  document.getElementById("atualizar-llm").addEventListener("click", executar);
  document.getElementById("llm-correlacao").addEventListener("change", executar);
})();
