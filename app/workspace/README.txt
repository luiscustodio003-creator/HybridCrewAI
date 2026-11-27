MÓDULO: workspace
FINALIDADE: Manter caminhos confinados à raiz resolvida, relatar cobertura sem ler conteúdos no scan e classificar e isolar anexos sem expor conteúdo.
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
- rejeição de directoria raiz ligada, ficheiros acima do limite e entradas especiais;
- classificação de ficheiros sensíveis por nome e conteúdo, com motivos estáveis;
- leitura limitada de anexos com verificação de ligações e tamanho;
- cópia de anexos para quarentena com SHA-256 e sem gravar texto do anexo;
- libertação só com token opaco e verificação final do SHA-256.
ESTRUTURA:
- __init__.py: API pública do módulo;
- paths.py: regras de validação e excepção tipada;
- scanner.py: percurso confinado e relatório de cobertura;
- sensitive.py: classificação sem exposição de conteúdo;
- quarantine.py: retenção e libertação de anexos com aprovação.
INTERFACE PÚBLICA:
- WorkspacePathError: erro de validação de caminho;
- validate_workspace_path(root, candidate, *, max_chars): devolve o caminho absoluto validado;
- IgnoreReason: motivos estáveis de ignorado (link, invalid-path, too-large, not-regular, unreadable);
- IgnoredFile: par caminho relativo/motivo;
- WorkspaceScan: lidos, ignorados, directórios ignorados, total no disco e cobertura;
- scan_workspace(root, *, max_chars, max_file_bytes): devolve a cobertura do workspace;
- SensitiveReason: motivos estáveis de classificação (filename, content);
- SensitiveFile: metadados do ficheiro classificado, sem conteúdo;
- classify_sensitive(root, relative, *, max_chars, max_file_bytes): classifica um ficheiro do workspace;
- QuarantineError: erro de quarentena ou aprovação inválida;
- QuarantineLimits: limites de caminho e tamanho dos anexos;
- QuarantinedAttachment: registo com caminho em quarentena, destino, SHA-256 e digest da aprovação;
- quarantine_attachment(root, source, *, relative_name, approval_token, limits): retém um anexo;
- release_quarantine(root, record_id, *, approval_token, limits): liberta um anexo após aprovação.
DEPENDÊNCIAS: biblioteca padrão (dataclasses, enum, hashlib, hmac, json, ntpath, os, pathlib, re, stat, uuid) e llm-egress para detecção de segredos.
CONFIGURAÇÃO: os limites são passados pelo chamador; os valores previstos vêm de HCW_MAX_WORKSPACE_PATH_CHARS e HCW_MAX_WORKSPACE_FILE_BYTES em app.core.config.
UTILIZAÇÃO: validate_workspace_path(settings.workspace_dir, "src/main.py", max_chars=settings.max_workspace_path_chars)
UTILIZAÇÃO: scan_workspace(settings.workspace_dir, max_chars=settings.max_workspace_path_chars, max_file_bytes=settings.max_workspace_file_bytes)
UTILIZAÇÃO: classify_sensitive(settings.workspace_dir, "anexo.txt", max_chars=settings.max_workspace_path_chars, max_file_bytes=settings.max_workspace_file_bytes)
UTILIZAÇÃO: quarantine_attachment(settings.workspace_dir, origem, relative_name="docs/anexo.txt", approval_token=token_da_ui, limits=QuarantineLimits(max_chars=settings.max_workspace_path_chars, max_file_bytes=settings.max_workspace_file_bytes))
TESTES: python -m pytest -q tests/unit/test_workspace_paths.py tests/security/test_phase05_paths.py tests/unit/test_workspace_scanner.py tests/security/test_phase05_quarantine.py
LIMITAÇÕES: o scanner não lê conteúdo; a classificação lê uma cópia limitada em memória e não devolve texto. Nenhum módulo protege contra substituição do ficheiro depois da validação; o chamador deve abrir com opções que não sigam ligações quando o sistema operativo as oferecer. A quarentena ainda não está ligada ao chat; essa integração pertence a tarefas posteriores. O token de aprovação é fornecido pelo chamador e só o seu digest é guardado; a UI deve gerar o token opaco.
SEGURANÇA: conteúdo de caminhos e anexos é tratado como dado não confiável; nenhum erro, registo, metadado ou relatório inclui conteúdo de ficheiros nem token em claro.
RELAÇÕES: prepara o terreno para ZIP, snapshots, diff e ecrãs locais das tarefas seguintes da Fase 5.
