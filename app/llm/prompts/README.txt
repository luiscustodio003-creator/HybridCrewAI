MÓDULO: llm.prompts

FINALIDADE: Guardar prompts versionados como dados locais, com identidade e hash verificáveis.

FUNCIONALIDADES: Cabeçalho `id`/`version`, SHA-256 do conteúdo no carregamento, rejeição de prompts inválidos e inserção de blocos não confiáveis apenas pelo delimitador de `llm.egress`.

ESTRUTURA:
- __init__.py — API pública.
- registry.py — carregamento, validação e renderização.
- system.md — prompt base do assistente.
- revisao.md — prompt de revisão.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas.

INTERFACE PÚBLICA: PromptRegistry, PromptRecord, PromptError, PromptNotFound, InvalidPromptVersion.

DEPENDÊNCIAS: internas — app.llm.egress; externas — nenhuma.

CONFIGURAÇÃO: `PromptRegistry(caminho)`; sem argumentos usa a pasta do próprio módulo.

UTILIZAÇÃO:
registro = PromptRegistry().get("sistema", 1)
prompt = PromptRegistry().render("revisao", untrusted={"codigo": texto})

TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_prompt_registry.py

LIMITAÇÕES: não resolve variáveis arbitrárias, não descarrega prompts e não interpreta Markdown como código.

RELAÇÕES: usa `app.llm.egress.wrap_untrusted`; será usado pelo roteador e pelos providers.
