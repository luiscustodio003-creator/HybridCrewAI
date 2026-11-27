MÓDULO: workspace
FINALIDADE: Manter caminhos confinados à raiz resolvida, relatar cobertura sem ler conteúdos no scan, classificar e isolar anexos sem expor conteúdo, ingerir ZIPs com validação completa antes de gravar, criar snapshots com rollback e undo verificáveis, registar auditoria e aplicar escritas atómicas com recuperação.
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
- libertação só com token opaco e verificação final do SHA-256;
- ingestão de ZIP com validação de todas as entradas em memória antes de gravar;
- rejeição de Zip Slip, caminhos absolutos, entradas especiais e ligações declaradas;
- limites de ficheiro, total, tamanho do ZIP, entradas, rácio e aninhamento;
- extração atómica em staging dentro do workspace, sem expor conteúdo no relatório;
- inventário de ficheiros com SHA-256 e limites de caminho, ficheiro, total e quantidade;
- snapshots gravados em staging e confirmados por manifesto com digest canónico;
- verificação de cada ficheiro do snapshot antes de qualquer rollback;
- rollback com undo automático do estado pós-alteração;
- limpeza do staging quando a gravação ou a aplicação falha antes do commit;
- auditoria JSONL com allowlist de metadados, sem conteúdo de ficheiros nem segredos;
- journal de operações pendentes e confirmadas com manifesto verificado por SHA-256;
- escrita em staging por operação, com substituição atómica só depois da confirmação;
- recuperação de operações interrompidas, com descarte de pendências e staging órfão;
- eventos de auditoria com task_id, correlation_id e nível (INFO, WARNING, ERROR).
ESTRUTURA:
- __init__.py: API pública do módulo;
- paths.py: regras de validação e excepção tipada;
- scanner.py: percurso confinado e relatório de cobertura;
- sensitive.py: classificação sem exposição de conteúdo;
- quarantine.py: retenção e libertação de anexos com aprovação;
- archive.py: validação e extração segura de ZIP;
- snapshot.py: inventário, digest e criação de snapshots;
- rollback.py: leitura verificada, restauro e undo;
- audit.py: registo JSONL com allowlist e limites;
- journal.py: manifestos de operação, staging e limpeza de órfãos;
- file_ops.py: escrita atómica e recuperação.
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
- release_quarantine(root, record_id, *, approval_token, limits): liberta um anexo após aprovação;
- ArchiveError: erro de arquivo rejeitado ou extração incompleta;
- ArchiveLimits: limites de caminho, bytes e entradas do ZIP;
- ArchiveEntry: metadados da entrada extraída, sem conteúdo;
- ArchiveReport: destino, entradas, total descomprimido e total comprimido;
- ingest_zip(root, source, *, destination, limits): valida e extrai um ZIP no workspace;
- SnapshotError: erro de snapshot inválido ou não verificado;
- SnapshotLimits: limites de caminho, ficheiro, total e quantidade do snapshot;
- SnapshotEntry: caminho, tamanho e SHA-256 de um ficheiro inventariado;
- Snapshot: snapshot confirmado com identificador, digest e entradas;
- create_snapshot(root, *, limits): cria um snapshot atómico do workspace;
- inventory_workspace(root, *, limits): devolve o inventário verificado do workspace;
- snapshot_digest(entries): calcula o digest canónico de um inventário;
- load_snapshot(root, snapshot_id, *, limits): lê e verifica um snapshot guardado;
- RollbackError: erro de rollback ou undo recusado, interrompido ou não verificado;
- RollbackReport: identificadores, digest e entradas do estado restaurado;
- UndoReport: identificador, digest e entradas do estado reposto pelo undo;
- rollback(root, snapshot_id, *, limits): restaura um snapshot e guarda o estado actual como undo;
- undo_rollback(root, undo_id, *, limits): desfaz um rollback;
- AuditError: erro de auditoria recusada ou inválida;
- AuditLimits: limites de registo, caminho, linha e ficheiro da auditoria;
- AuditTrail: registo estruturado de eventos em JSONL;
- FileChange: alteração pedida com caminho relativo, bytes e digest;
- FileOpLimits: limites de caminho, bytes, ficheiros e manifesto da operação;
- FileOpReport: identificador, ficheiros e digest da operação confirmada;
- FileOpsError: erro de escrita atómica, recuperação ou caminho inseguro;
- RecoveryReport: operações restauradas e descendentes descartadas;
- apply_atomic(root, changes, *, context, audit, limits): grava alterações com journal e auditoria;
- recover_workspace(root, *, context, audit, limits): recupera operações interrompidas.
DEPENDÊNCIAS: biblioteca padrão (collections.abc, dataclasses, enum, hashlib, hmac, io, json, ntpath, os, pathlib, re, shutil, stat, uuid, zipfile) e llm-egress para detecção de segredos.
CONFIGURAÇÃO: os limites são passados pelo chamador; os valores previstos vêm de HCW_MAX_WORKSPACE_PATH_CHARS, HCW_MAX_WORKSPACE_FILE_BYTES, HCW_MAX_ZIP_BYTES, HCW_MAX_ZIP_ENTRIES e HCW_MAX_ZIP_NESTING em app.core.config. A auditoria usa `.file-ops/audit.jsonl`; o journal e o staging usam `.file-ops/journal/` e `.file-ops/staging/`, todos excluídos de snapshots e undo.
UTILIZAÇÃO: validate_workspace_path(settings.workspace_dir, "src/main.py", max_chars=settings.max_workspace_path_chars)
UTILIZAÇÃO: scan_workspace(settings.workspace_dir, max_chars=settings.max_workspace_path_chars, max_file_bytes=settings.max_workspace_file_bytes)
UTILIZAÇÃO: classify_sensitive(settings.workspace_dir, "anexo.txt", max_chars=settings.max_workspace_path_chars, max_file_bytes=settings.max_workspace_file_bytes)
UTILIZAÇÃO: quarantine_attachment(settings.workspace_dir, origem, relative_name="docs/anexo.txt", approval_token=token_da_ui, limits=QuarantineLimits(max_chars=settings.max_workspace_path_chars, max_file_bytes=settings.max_workspace_file_bytes))
UTILIZAÇÃO: ingest_zip(settings.workspace_dir, origem, destination="inbox", limits=ArchiveLimits(max_chars=settings.max_workspace_path_chars, max_file_bytes=settings.max_workspace_file_bytes, max_total_bytes=20_000_000, max_zip_bytes=settings.max_zip_bytes, max_entries=settings.max_zip_entries, max_ratio=100, max_nesting=settings.max_zip_nesting))
UTILIZAÇÃO: apply_atomic(settings.workspace_dir, alteracoes, context=contexto, audit=auditoria, limits=FileOpLimits(max_chars=settings.max_workspace_path_chars, max_file_bytes=settings.max_workspace_file_bytes))
UTILIZAÇÃO: recover_workspace(settings.workspace_dir, context=contexto, audit=auditoria, limits=FileOpLimits(max_chars=settings.max_workspace_path_chars, max_file_bytes=settings.max_workspace_file_bytes))
TESTES: python -m pytest -q tests/unit/test_workspace_paths.py tests/security/test_phase05_paths.py tests/unit/test_workspace_scanner.py tests/security/test_phase05_quarantine.py tests/security/test_phase05_zip.py tests/integration/test_workspace_snapshot.py tests/recovery/test_workspace_interrupt.py tests/recovery/test_workspace_audit_attack.py
LIMITAÇÕES: o scanner não lê conteúdo; a classificação e a ingestão de ZIP leem cópias limitadas em memória e não devolvem texto. Nenhum módulo protege contra substituição do ficheiro depois da validação; o chamador deve abrir com opções que não sigam ligações quando o sistema operativo as oferecer. A quarentena e a ingestão de ZIP ainda não estão ligadas ao chat; essa integração pertence a tarefas posteriores. O token de aprovação é fornecido pelo chamador e só o seu digest é guardado; a UI deve gerar o token opaco. O limite de aninhamento usa o nome da entrada e a assinatura dos bytes, não uma descompressão recursiva. As operações de ficheiro são consistentes com o último commit válido após `recover_workspace`, mesmo quando o processo morre antes ou depois da confirmação; a atomicidade multi-ficheiro ao nível do sistema não é garantida sem cooperação dos leitores. Snapshots, undo e escritas atómicas ainda não estão ligados à UI nem ao fluxo de aprovação.
SEGURANÇA: conteúdo de caminhos, anexos, ZIPs e snapshots é tratado como dado não confiável; nenhum erro, registo, metadado ou relatório inclui conteúdo de ficheiros nem token em claro. Nenhum ficheiro dentro de um ZIP é escrito ou executado antes da validação completa de todas as entradas. Nenhum snapshot é aplicado sem verificação de manifesto, de caminhos e de SHA-256 de todos os ficheiros. Nenhum manifesto de journal guarda conteúdo, tokens ou campos fora da allowlist; um journal adulterado é recusado e nenhuma alteração pode escrever dentro de `.file-ops`.
RELAÇÕES: prepara o terreno para diff, aprovação de alterações e ecrãs locais das tarefas seguintes da Fase 5.
