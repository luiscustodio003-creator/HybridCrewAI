MÓDULO: llm

FINALIDADE: Definir os contratos, o consentimento cloud e a política de egress do gateway de modelos, sem expor tipos de SDK externo.

FUNCIONALIDADES: Modelos de pedido, resposta e erro; validação de timeout; redacção de segredos; consentimento persistido sem credenciais; recusa de cloud sem autorização.

ESTRUTURA:
- __init__.py — API pública do módulo.
- contracts.py — contratos, enumerações e validações.
- consent.py — consentimento cloud e tipo de conta Gemini em SQLite.
- egress/ — redacção, autorização e delimitação de conteúdo não confiável.
- prompts/ — prompts versionados e renderização segura.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas do projecto.

INTERFACE PÚBLICA: ProviderKind, ErrorKind, ModelRequest, ModelResponse, ProviderError, AccountType, CloudConsentStore, EgressPolicy, PromptRegistry, PromptRecord.

DEPENDÊNCIAS: internas — app.core.logging.SecretRegistry; externas — sqlite3 e urllib da stdlib.

CONFIGURAÇÃO: CLOUD_CONSENT_DEFAULT e GEMINI_ACCOUNT_TYPE_DEFAULT em app.core.config.defaults; o timeout é obrigatório em cada pedido.

UTILIZAÇÃO:
from app.llm import ModelRequest, ProviderKind
pedido = ModelRequest(provider=ProviderKind.FAKE, model="fake-1", prompt="Diz olá", timeout_s=5.0, task_id="HCW-02-003", correlation_id="corr-1")

TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_llm_contracts.py tests/unit/test_llm_consent.py tests/unit/test_prompt_registry.py tests/security/test_egress.py

LIMITAÇÕES: não contacta fornecedores reais, não escolhe modelos nem impõe orçamento; essas responsabilidades pertencem às tarefas seguintes.

RELAÇÕES: usado pelo planeado roteador, egress, budget, providers e CLI; usa app.core.logging.
