(function () {
  "use strict";

  const api = window.hcwApi;
  const campoFicheiro = document.getElementById("anexo-ficheiro");
  const botaoEnviar = document.getElementById("anexo-enviar");
  const botaoAprovar = document.getElementById("anexo-aprovar");
  const estado = document.getElementById("estado-anexo");
  let identificador = null;

  function contexto() {
    const dados = {
      task_id: document.getElementById("aprovacao-tarefa").value.trim(),
      correlation_id: document.getElementById("aprovacao-correlacao").value.trim(),
      diff_hash: document.getElementById("aprovacao-diff").value.trim(),
    };
    if (!dados.task_id || !dados.correlation_id || !dados.diff_hash) return null;
    const token = window.hcwAprovacaoToken ? window.hcwAprovacaoToken() : null;
    if (!token || !document.getElementById("token").value.trim()) return null;
    return Object.assign(dados, { token: token });
  }

  function verificar() {
    const ficheiro = campoFicheiro.files && campoFicheiro.files[0];
    botaoEnviar.disabled = !ficheiro || contexto() === null;
    botaoAprovar.disabled = identificador === null || contexto() === null;
  }

  function lerBase64(ficheiro) {
    return new Promise(function (resolver, rejeitar) {
      const leitor = new FileReader();
      leitor.onload = function () {
        const valor = String(leitor.result);
        const indice = valor.indexOf(",");
        resolver(indice === -1 ? valor : valor.slice(indice + 1));
      };
      leitor.onerror = function () {
        rejeitar(new Error("Não foi possível ler o ficheiro."));
      };
      leitor.readAsDataURL(ficheiro);
    });
  }

  async function recarregarChat() {
    if (window.hcwChatRecarregar) await window.hcwChatRecarregar();
  }

  async function enviar() {
    const ficheiro = campoFicheiro.files && campoFicheiro.files[0];
    const dados = contexto();
    if (!ficheiro || !dados) {
      estado.textContent = "Preencha a aprovação e escolha um ZIP.";
      return;
    }
    try {
      const conteudo = await lerBase64(ficheiro);
      const registro = await api.postJson("/api/attachments", {
        task_id: dados.task_id,
        correlation_id: dados.correlation_id,
        diff_hash: dados.diff_hash,
        approval_token: dados.token,
        filename: ficheiro.name,
        content_base64: conteudo,
      });
      identificador = registro.attachment_id;
      await recarregarChat();
      estado.textContent = "Anexo em quarentena: " + identificador;
    } catch (erro) {
      estado.textContent = erro.message;
    } finally {
      verificar();
    }
  }

  async function aprovar() {
    const dados = contexto();
    if (!dados || !identificador) {
      estado.textContent = "Não há um anexo aprovado para libertar.";
      return;
    }
    try {
      const resposta = await api.postJson("/api/attachments/release", {
        attachment_id: identificador,
        task_id: dados.task_id,
        correlation_id: dados.correlation_id,
        diff_hash: dados.diff_hash,
        approval_token: dados.token,
      });
      const relatorio = resposta.report || {};
      const texto =
        "Cobertura: " +
        String((relatorio.lidos || []).length) +
        " lidos, " +
        String((relatorio.ignorados || []).length) +
        " ignorados.";
      identificador = null;
      campoFicheiro.value = "";
      await recarregarChat();
      estado.textContent = texto;
    } catch (erro) {
      estado.textContent = erro.message;
    } finally {
      verificar();
    }
  }

  campoFicheiro.addEventListener("change", function () {
    if (campoFicheiro.files && campoFicheiro.files[0]) {
      estado.textContent = "Ficheiro selecionado: " + campoFicheiro.files[0].name;
    }
    verificar();
  });
  document.getElementById("aprovacao-tarefa").addEventListener("input", verificar);
  document.getElementById("aprovacao-correlacao").addEventListener("input", verificar);
  document.getElementById("aprovacao-diff").addEventListener("input", verificar);
  botaoEnviar.addEventListener("click", enviar);
  botaoAprovar.addEventListener("click", aprovar);
  api.registar(verificar);
})();
