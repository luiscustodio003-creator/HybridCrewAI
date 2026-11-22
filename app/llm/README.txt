MÓDULO: llm

FINALIDADE: Definir os contratos imutáveis usados pelo gateway de modelos, sem expor tipos de SDK externo.

FUNCIONALIDADES: Modelos de pedido, resposta e erro; identificadores de fornecedor e erro; validação de timeout positivo; redacção de segredos em representações textuais.

ESTRUTURA:
- __init__.py — API pública do módulo.
- contracts.py — contratos, enumerações e validações.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas do projecto.

INTERFACE PÚBLICA: ProviderKind, ErrorKind, ModelRequest, ModelResponse, ProviderError.

DEPENDÊNCIAS: internas — app.core.logging.SecretRegistry; externas — nenhuma.

CONFIGURAÇÃO: nenhuma; o timeout é obrigatório em cada pedido.

UTILIZAÇÃO:
from app.llm import ModelRequest, ProviderKind
pedido = ModelRequest(provider=ProviderKind.FAKE, model="fake-1", prompt="Diz olá", timeout_s=5.0, task_id="HCW-02-003", correlation_id="corr-1")

TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_llm_contracts.py

LIMITAÇÕES: não contacta fornecedores, não escolhe modelos, não impõe egress nem orçamento; essas responsabilidades pertencem às tarefas seguintes.

RELAÇÕES: usado pelo planeado roteador, egress, budget, providers e CLI; usa app.core.logging.
