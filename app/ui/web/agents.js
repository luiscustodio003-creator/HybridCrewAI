(function () {
  "use strict";

  const api = window.hcwApi;

  function mostrarAgentes(dados) {
    const lista = document.getElementById("agentes");
    lista.replaceChildren();
    if (!Array.isArray(dados) || dados.length === 0) {
      api.item(lista, "Sem agentes registados.");
      return;
    }
    for (const agente of dados) {
      api.item(
        lista,
        [
          agente.agent_id,
          agente.nome,
          "v" + agente.versao,
          agente.entrada,
          agente.saida,
        ]
          .filter(Boolean)
          .join(" · ")
      );
    }
  }

  async function atualizar() {
    try {
      mostrarAgentes(await api.getJson("/api/agents"));
    } catch (erro) {
      api.aviso(erro.message);
    }
  }

  api.registar(atualizar);
  document.getElementById("atualizar-agentes").addEventListener("click", atualizar);
})();
