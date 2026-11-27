MÓDULO: workspace
FINALIDADE: Manter todos os caminhos de ficheiro confinados à raiz resolvida do workspace, antes de qualquer abertura.
FUNCIONALIDADES:
- validação de caminhos relativos com separadores '/' ou '\';
- rejeição de caminhos absolutos, UNC, travessia '..' e componente '.';
- rejeição de nomes reservados do Windows, incluindo extensão;
- rejeição de caracteres de controlo, ponto ou espaço no fim dos componentes;
- rejeição de caminhos acima do limite de caracteres;
- rejeição de symlinks e junctions em qualquer componente existente;
- verificação final de contenção na raiz resolvida.
ESTRUTURA:
- __init__.py: API pública do módulo;
- paths.py: regras de validação e excepção tipada.
INTERFACE PÚBLICA:
- WorkspacePathError: erro de validação de caminho;
- validate_workspace_path(root, candidate, *, max_chars): devolve o caminho absoluto validado.
DEPENDÊNCIAS: biblioteca padrão (ntpath, os, pathlib, stat).
CONFIGURAÇÃO: o limite é passado pelo chamador; o valor previsto vem de HCW_MAX_WORKSPACE_PATH_CHARS em app.core.config.
UTILIZAÇÃO: validate_workspace_path(settings.workspace_dir, "src/main.py", max_chars=settings.max_workspace_path_chars)
TESTES: python -m pytest -q tests/unit/test_workspace_paths.py tests/security/test_phase05_paths.py
LIMITAÇÕES: o módulo não cria ficheiros, não lê conteúdo e não protege contra substituição do caminho depois da validação; o chamador deve abrir o ficheiro com opções que não sigam ligações quando o sistema operativo as oferecer.
SEGURANÇA: conteúdo de caminhos é tratado como dado não confiável; nenhum erro inclui conteúdo de ficheiros.
RELAÇÕES: prepara o terreno para escrita de workspace, ZIP, anexos, snapshots e diff das tarefas seguintes da Fase 5.
