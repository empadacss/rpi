# CentralOS2 para Raspberry Pi

Este repositório reúne o script `centralos2.py` e a pasta
`bitcoin_mining_automation`, permitindo executar um ambiente de
monitoramento e automação de uma sala de mineração em uma Raspberry Pi.

## Requisitos

* Python 3.10+ (recomendado 3.11).
* Bibliotecas opcionais:
  * `pymodbus` para controle Modbus TCP.
  * `bleak` e `atc_mi_interface` para sensores BLE Xiaomi.
  * `schedule` para rotinas programadas.
* A pasta `bitcoin_mining_automation` fornecida neste repositório (já
  presente neste clone) para reaproveitar arquivos de configuração.

## Instalação

1. Configure o ambiente virtual (opcional):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r bitcoin_mining_automation/backend/requirements.txt
   ```

2. Crie (se necessário) o arquivo `.env` e `config/devices.yaml`
   reutilizando os modelos da pasta `bitcoin_mining_automation`.

## Uso

### Monitoramento contínuo

```bash
python3 centralos2.py run
```

Opções úteis:

* `--verbose`: exibe logs no terminal enquanto grava no arquivo
  `~/.centralos2/centralos2.log`.
* `--interval 15`: define o intervalo de atualização (segundos) usado
  para impressões periódicas e alguns loops.
* `--non-interactive`: desabilita o console interativo, ideal quando o
  processo é executado como serviço.

### Consulta rápida

```bash
python3 centralos2.py status
```

Mostra uma tabela com o último estado conhecido (sem iniciar os loops).

## Armazenamento de dados

O script persiste informações em `~/.centralos2/`:

* `centralos2.log`: arquivo de log rotativo.
* `csv/multimeter.csv`: histórico do multimedidor ABB.
* `asics.json`: cadastro de ASICs.
* `rotinas_automacao.json`: agendamentos criados no console.

## Conceitos herdados de `bitcoin_mining_automation`

* Leitura das configurações de dispositivos (`config/devices.yaml`).
* Estrutura de automação e regras de segurança.
* Organização de diretórios para logs e históricos.

A nova implementação simplifica a execução em Raspberry Pi, mantendo o
conceito modular do projeto original e oferecendo um console interativo
leve para operação diária.
