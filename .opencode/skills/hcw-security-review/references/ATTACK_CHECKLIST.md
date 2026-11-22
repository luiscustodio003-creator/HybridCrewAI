# Lista de ataques a testar

## Ficheiros e workspace
- `..\..\`, caminhos absolutos, nomes reservados do Windows, caminhos longos
- symlink e junction para fora do workspace
- ZIP: Zip Slip, ZIP bomb (tamanho e rácio), symlinks, ZIP dentro de ZIP além do limite
- escrita interrompida a meio (a pasta tem de ficar consistente)

## Modelo e cloud
- ficheiro com «ignora as instruções anteriores»; marcador de fecho de bloco forjado
- chave falsa (`AKIA...`, `sk-...`) num ficheiro: não pode aparecer no payload enviado
- ficheiro `.env`: marcado como proibido de seguir para a cloud
- agente devolve `approved=true`: sem efeito

## Execução
- ler fora da pasta, abrir rede, ler variáveis de ambiente com credenciais
- ciclo infinito, memória excessiva, fork bomb
- scripts dentro de ZIP nunca correm automaticamente

## Interface local
- pedido sem token; `Origin` falso; escuta fora de 127.0.0.1

## Ferramentas do computador
- nome de aplicação com `&`, `;`, `|`, aspas; fechar o próprio assistente
- acção irreversível sem o botão de confirmação
