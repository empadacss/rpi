# Sistema de Automação de Mineração de Bitcoin

Este repositório contém scripts e automações para preparar um ambiente Ubuntu focado em mineradores ASIC e dispositivos auxiliares. O destaque é o instalador `bitcoin_mining_automation/scripts/install_ubuntu_raspberry_pi.sh`, que realiza a preparação completa do sistema.

## Como baixar o script de instalação

O ramo principal usado para distribuição é `main`. Caso você esteja testando uma ramificação alternativa, ajuste o caminho conforme necessário.

```bash
wget https://raw.githubusercontent.com/empadaccs/rpi/main/bitcoin_mining_automation/scripts/install_ubuntu_raspberry_pi.sh
chmod +x install_ubuntu_raspberry_pi.sh
sudo ./install_ubuntu_raspberry_pi.sh
```

Se o arquivo for movido para outro ramo ou diretório, atualize a URL substituindo `main` pelo ramo desejado ou ajustando o caminho após o nome do repositório.

## Como tornar seu código público no GitHub

1. **Crie um repositório**
   - Acesse [https://github.com/new](https://github.com/new).
   - Defina o nome do repositório e selecione a visibilidade **Public**.
   - Opcionalmente, adicione um README, `.gitignore` e licença.

2. **Associe o repositório remoto ao seu código local**
   ```bash
   git init                # caso ainda não exista um repositório git local
   git remote add origin git@github.com:<usuario>/<repositorio>.git
   ```
   Utilize a URL HTTPS (`https://github.com/...`) se preferir autenticação via token em vez de SSH.

3. **Confirme os arquivos e envie para o GitHub**
   ```bash
git add .
git commit -m "Primeiro commit público"
git push -u origin main       # ajuste o nome do ramo se necessário
   ```

4. **Verifique a visibilidade**
   - Acesse o repositório no navegador e confirme que o selo "Public" aparece próximo ao nome.
   - Compartilhe a URL com colaboradores ou torne o projeto privado posteriormente em *Settings > General > Danger Zone > Change repository visibility* se precisar restringir o acesso.

## Suporte

Abra uma issue ou pull request em caso de dúvidas, sugestões ou problemas durante a instalação.
