# Modelo de ameaças
Cada ameaça liga-se a uma fase e a um teste que a ataca de facto (Skill `hcw-security-review`).

| Ameaça | Fase | Contramedida | Teste |
|---|---|---|---|
| Prompt injection em ficheiros, páginas ou binários | 2, 7, 13 | Conteúdo como dados delimitados; agentes sem ferramentas directas; marcador de fecho não forjável | Fixtures com instruções hostis |
| Fuga de segredos para a cloud | 2, 5 | Scan, redacção e exclusão antes do envio; interruptor por projecto | Servidor falso capta o payload |
| Aprovação forjada pelo modelo | 4, 12 | Token único emitido só pela interface, ligado ao hash do diff | Agente devolve approved=true sem efeito |
| ZIP malicioso (Zip Slip, bomb, symlinks) | 5 | Limites, validação de caminhos, quarentena | Arquivos hostis em fixtures |
| Path traversal e symlinks exteriores | 5 | Canonicalização; workspace como unidade de permissões | Bateria de caminhos |
| Execução de código gerado ou de terceiros | 4, 6 | Isolamento obrigatório; recusa sem mecanismo seguro; sem rede nem credenciais | Testes de fuga |
| Injecção de comandos em ferramentas | 12 | Parâmetros tipados, sem shell, sem código escrito pelo modelo | Nomes com & ; | |
| Fecho do processo ou janela errada | 12 | Correspondência por processos em execução; protecção do próprio assistente | Teste de auto-protecção |
| Interface local atacada via browser | 3 | 127.0.0.1, token de sessão, verificação de Origin | Pedidos com Origin falso |
| Dependência ou ferramenta comprometida | 0, 13 | Versões fixadas, pip-audit, origens oficiais, instalação com aprovação | Verificação no CI |
| Perda de trabalho em falhas | 1, 5, 9 | Snapshots, checkpoints, testes de kill | Testes de recuperação |
| Custos e quotas fora de controlo | 2, 9 | Orçamento por tarefa, pausa por quota, botão de paragem | Esgotar orçamentos de propósito |
| Acção reportada como feita sem o ter sido | 1, 12 | ToolResult com verificação; unverified nunca é sucesso | Aplicação inexistente |
