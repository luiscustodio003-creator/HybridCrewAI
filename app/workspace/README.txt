MÓDULO: workspace
FINALIDADE: Manter todos os caminhos de ficheiro confinados à raiz resolvida do workspace e relatar cobertura sem ler conteúdos.
FUNCIONALIDADES:
- validação de caminhos relativos com separadores '/' ou '\';
- rejeição de caminhos absolutos, UNC, travessia '..' e componente '.';
- rejeição de nomes reservados do Windows, incluindo extensão;
- rejeição de caracteres de controlo, ponto ou espaço no fim dos componentes;
- rejeição de caminhos acima do limite de caracteres;
- rejeição de symlinks e junctions em qualquer componente existente;
- verificação final de contenção na raiz resolvida;
- scanner de cobertura com ficheiros lidos e ignorados, cada um com motivo estável;
- não seguimento de symlinks, junctions ou directórios ligados durante o scan;
- rejeição de directoria raiz ligada, ficheiros acima do limite e entradas especiais.
ESTRUTURA:
- __init__.py: API pública do módulo;
- paths.py: regras de validação e excepção tipada;
- scanner.py: percurso confinado e relatório de cobertura.
INTERFACE PÚBLICA:
- WorkspacePathError: erro de validação de caminho;
- validate_workspace_path(root, candidate, *, max_chars): devolve o caminho absoluto validado;
- IgnoreReason: motivos estáveis de ignorado (link, invalid-path, too-large, not-regular, unreadable);
- IgnoredFile: par caminho relativo/motivo;
- WorkspaceScan: lidos, ignorados, directórios ignorados, total no disco e cobertura;
- scan_workspace(root, *, max_chars, max_file_bytes): devolve a cobertura do workspace.
DEPENDÊNCIAS: biblioteca padrão (dataclasses, enum, ntpath, os, pathlib, stat).
CONFIGURAÇÃO: os limites são passados pelo chamador; os valores previstos vêm de HCW_MAX_WORKSPACE_PATH_CHARS e HCW_MAX_WORKSPACE_FILE_BYTES em app.core.config.
UTILIZAÇÃO: validate_workspace_path(settings.workspace_dir, "src/main.py", max_chars=settings.max_workspace_path_chars)
UTILIZAÇÃO: scan_workspace(settings.workspace_dir, max_chars=settings.max_workspace_path_chars, max_file_bytes=settings.max_workspace_file_bytes)
TESTES: python -m pytest -q tests/unit/test_workspace_paths.py tests/security/test_phase05_paths.py tests/unit/test_workspace_scanner.py
LIMITAÇÕES: o módulo não cria ficheiros, não lê conteúdo e não protege contra substituição do caminho depois da validação; o chamador deve abrir o ficheiro com opções que não sigam ligações quando o sistema operativo as oferecer. Directórios ilegíveis são ignorados com motivo explícito, mas o seu conteúdo não pode ser contado.
SEGURANÇA: conteúdo de caminhos é tratado como dado não confiável; nenhum erro inclui conteúdo de ficheiros.
RELAÇÕES: prepara o terreno para escrita de workspace, ZIP, anexos, snapshots e diff das tarefas seguintes da Fase 5.
