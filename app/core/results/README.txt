# core/results — resultados verificados

FINALIDADE: representar o resultado de uma ferramenta sem confundir sucesso com evidência.

ESTADOS: done (com evidência obrigatória), unverified, failed (com error), ask (com question) e started (em curso).

ESTRUTURA: statuses.py (ToolStatus); tool_result.py (ToolResult, ToolResultError, new_tool_result, validar_tool_result); __init__.py (API pública).

INTERFACE PÚBLICA: ToolResult, ToolResultError, ToolStatus, new_tool_result, validar_tool_result.
DEPENDÊNCIAS: apenas biblioteca padrão (dataclasses, enum).
UTILIZAÇÃO: novo = new_tool_result(ToolStatus.DONE, 'Ficheiro criado', evidence=('caminho/relatorio.txt',)); validar_tool_result(novo).
TESTES: python -m pytest -q tests/contracts/test_tool_result.py
LIMITAÇÕES: o esquema valida presença e não cadeias de confiança; a evidência é textual e não é verificada contra ficheiros.
