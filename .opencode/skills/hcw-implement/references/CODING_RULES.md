# Regras de código

- Máximo 300 linhas por ficheiro (aviso aos 200) e 40 linhas por função.
- Um ficheiro, uma responsabilidade; o nome diz o que faz.
- Importar só pela API pública do módulo (`__init__.py`); sem dependências circulares.
- Excepções tipadas, com causa e acção sugerida na mensagem.
- Toda a chamada a modelo, rede ou subprocesso tem timeout.
- Importações pesadas preguiçosas (no primeiro uso).
- Todo o evento leva `correlation_id`, `task_id`, `agent`, `phase`.
- Tipagem completa nas interfaces públicas; docstring em PT-PT.
- Identificadores e nomes de ficheiros em inglês; comentários e documentação em PT-PT.
- Segredos nunca em código, logs ou testes (usar valores falsos óbvios).
