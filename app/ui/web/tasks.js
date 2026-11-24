(function () {
  "use strict";

  const estado = document.getElementById("estado");
  const recarregar = [];

  function token() {
    return document.getElementById("token").value.trim();
  }

  function cabecalhos() {
    return { Authorization: "Bearer " + token() };
  }

  async function resposta(caminho, opcoes) {
    const respostaHttp = await fetch(caminho, opcoes);
    if (!respostaHttp.ok) {
      throw new Error("Pedido recusado: " + respostaHttp.status);
    }
    return respostaHttp;
  }

  async function getJson(caminho) {
    const respostaHttp = await resposta(caminho, { headers: cabecalhos() });
    return respostaHttp.json();
  }

  async function postJson(caminho, corpo) {
    const opcoes = {
      method: "POST",
      headers: Object.assign({ "Content-Type": "application/json" }, cabecalhos()),
      body: JSON.stringify(corpo),
    };
    const respostaHttp = await resposta(caminho, opcoes);
    return respostaHttp.json();
  }

  function aviso(mensagem) {
    estado.textContent = mensagem;
  }

  function item(lista, texto) {
    const elemento = document.createElement("li");
    elemento.textContent = texto;
    lista.appendChild(elemento);
  }

  function mostrarTarefas(dados) {
    const lista = document.getElementById("tarefas");
    lista.replaceChildren();
    if (!Array.isArray(dados) || dados.length === 0) {
      item(lista, "Sem tarefas registadas.");
      return;
    }
    for (const tarefa of dados) {
      item(
        lista,
        [tarefa.task_id, tarefa.status, tarefa.title, tarefa.agent, tarefa.phase]
          .filter(Boolean)
          .join(" · ")
      );
    }
  }

  async function atualizarTarefas() {
    try {
      mostrarTarefas(await getJson("/api/tasks"));
      aviso("Tarefas atualizadas.");
    } catch (erro) {
      aviso(erro.message);
    }
  }

  async function ligar() {
    await atualizarTarefas();
    for (const funcao of recarregar) {
      await funcao();
    }
  }

  window.hcwApi = {
    aviso: aviso,
    cabecalhos: cabecalhos,
    getJson: getJson,
    item: item,
    postJson: postJson,
    registar: function (funcao) {
      recarregar.push(funcao);
    },
  };

  document.getElementById("ligar").addEventListener("click", ligar);
  document.getElementById("atualizar-tarefas").addEventListener("click", atualizarTarefas);
})();
