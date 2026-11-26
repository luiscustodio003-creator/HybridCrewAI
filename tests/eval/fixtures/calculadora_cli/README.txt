Calculadora de linha de comandos usada como caso dourado da Fase 4.

Ficheiros:
- main.py: operações somar e subtrair com argparse.
- test_main.py: quatro testes executados com pytest real pelo SimpleRunner.

Uso local:
  python main.py somar 2 3
  python main.py subtrair 7 4

O caso dourado não lê estes ficheiros dentro do subprocesso. O teste de
integração lê o conteúdo no processo de teste, incorpora-o no comando e o
executor grava-o na pasta temporária autorizada antes de correr pytest.
