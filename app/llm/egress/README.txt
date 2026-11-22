MÓDULO: llm.egress

FINALIDADE: Impedir que segredos e conteúdo não confiável saiam sem controlo, e recusar pedidos cloud sem consentimento.

FUNCIONALIDADES: Redacção de corpo, cabeçalhos e URL; política local/cloud; autorização antes de socket; delimitação de conteúdo não confiável; rejeição de marcadores forjados.

ESTRUTURA:
- __init__.py — API pública.
- secret_scan.py — detecção e redacção de segredos.
- policy.py — autorização e envio HTTP com urllib da stdlib.
- untrusted_wrap.py — marcadores de conteúdo não confiável.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas.

INTERFACE PÚBLICA: EgressPolicy, CloudDenied, CloudConsent, redact_text, redact_mapping, contem_segredo, wrap_untrusted, UntrustedContentError, INICIO, FIM.

DEPENDÊNCIAS: internas — app.core.logging, app.llm.egress; externas — urllib e http.server da stdlib apenas em testes.

CONFIGURAÇÃO: EgressPolicy(allow_local=True, allow_cloud=False) por omissão; consentimento injectado por chamador.

UTILIZAÇÃO:
politica = EgressPolicy()
estado, texto = politica.send_json(url, {"Content-Type": "application/json"}, {"prompt": wrap_untrusted("texto")})

TESTES: .venv\Scripts\python.exe -m pytest -q tests/security/test_egress.py

LIMITAÇÕES: não descobre segredos arbitrários sem padrão conhecido; não implementa lista de domínios nem consentimento persistente; não substitui revisão de prompt injection no modelo.

RELAÇÕES: usado pelo roteador e pelos providers; usa app.core.logging.
