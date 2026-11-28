(function () {
  "use strict";

  const api = window.hcwApi;
  const botao = document.getElementById("aprovar");
  const estado = document.getElementById("estado-aprovacao");
  let ultimoToken = null;
  let controlador = null;

  function tratarQuadro(quadro) {
    const linha = quadro.split("\n").find(function (parte) {
      return parte.startsWith("data:");
    });
    if (!linha) return;
    let evento;
    try {
      evento = JSON.parse(linha.slice(5).trim());
    } catch (erro) {
      return;
    }
    if (evento.kind === "create.plano") {
      botao.hidden = false;
      botao.disabled = false;
      estado.textContent = "Plano pronto para aprovação.";
    }
  }

  function parar() {
    if (controlador !== null) controlador.abort();
    controlador = null;
  }

  async function observarPlanos() {
    parar();
    controlador = new AbortController();
    try {
      const respostaHttp = await fetch("/api/events", {
        headers: api.cabecalhos(),
        signal: controlador.signal,
      });
      if (!respostaHttp.ok) throw new Error("Fluxo recusado: " + respostaHttp.status);
      const leitor = respostaHttp.body.getReader();
      const descodificador = new TextDecoder();
      let buffer = "";
      while (true) {
        const parte = await leitor.read();
        if (parte.done) break;
        buffer += descodificador.decode(parte.value, { stream: true });
        const quadros = buffer.split("\n\n");
        buffer = quadros.pop();
        for (const quadro of quadros) tratarQuadro(quadro);
      }
    } catch (erro) {
      if (erro.name !== "AbortError") estado.textContent = erro.message;
    } finally {
      parar();
    }
  }

  async function aprovar() {
    const corpo = {
      task_id: document.getElementById("aprovacao-tarefa").value.trim(),
      correlation_id: document.getElementById("aprovacao-correlacao").value.trim(),
      diff_hash: document.getElementById("aprovacao-diff").value.trim(),
    };
    try {
      const registro = await api.postJson("/api/approvals", corpo);
      ultimoToken = registro.token;
      estado.textContent = "Aprovação emitida.";
    } catch (erro) {
      estado.textContent = erro.message;
    }
  }

  window.hcwAprovacaoToken = function () {
    return ultimoToken;
  };

  api.registar(function () {
    observarPlanos().catch(function () {});
  });
  botao.addEventListener("click", aprovar);
})();
