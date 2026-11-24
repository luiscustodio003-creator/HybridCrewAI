(function () {
  "use strict";

  const api = window.hcwApi;
  const lista = document.getElementById("eventos");
  const botaoIniciar = document.getElementById("iniciar-eventos");
  const botaoParar = document.getElementById("parar-eventos");
  let controlador = null;

  function caminho() {
    const parametros = new URLSearchParams();
    const correlacao = document.getElementById("evento-correlacao").value.trim();
    const nivel = document.getElementById("evento-nivel").value.trim();
    if (correlacao) parametros.set("correlation_id", correlacao);
    if (nivel) parametros.set("level", nivel);
    const consulta = parametros.toString();
    return consulta ? "/api/events?" + consulta : "/api/events";
  }

  function adicionar(evento) {
    const li = document.createElement("li");
    li.textContent = [
      evento.occurred_at,
      evento.level,
      evento.kind,
      evento.correlation_id,
      evento.task_id,
      evento.message,
    ]
      .filter(Boolean)
      .join(" · ");
    lista.appendChild(li);
    while (lista.childElementCount > 200) {
      lista.removeChild(lista.firstElementChild);
    }
  }

  function tratarQuadro(quadro) {
    const linha = quadro.split("\n").find(function (parte) {
      return parte.startsWith("data:");
    });
    if (!linha) return;
    try {
      adicionar(JSON.parse(linha.slice(5).trim()));
    } catch (erro) {
      api.aviso("Evento inválido recebido.");
    }
  }

  function parar() {
    if (controlador !== null) controlador.abort();
    controlador = null;
    botaoIniciar.disabled = false;
    botaoParar.disabled = true;
  }

  async function iniciar() {
    parar();
    lista.replaceChildren();
    controlador = new AbortController();
    botaoIniciar.disabled = true;
    botaoParar.disabled = false;
    try {
      const respostaHttp = await fetch(caminho(), {
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
      if (erro.name !== "AbortError") api.aviso(erro.message);
    } finally {
      parar();
    }
  }

  botaoIniciar.addEventListener("click", iniciar);
  botaoParar.addEventListener("click", parar);
  document.getElementById("evento-correlacao").addEventListener("change", iniciar);
  document.getElementById("evento-nivel").addEventListener("change", iniciar);
})();
