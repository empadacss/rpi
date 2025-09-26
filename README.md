# CentralOS2 Modular Control Suite

Este repositório entrega uma versão setorizada e observável do sistema `centralos2` para controle e monitoramento de fazendas de mineração, com pipeline de dados pronto para alimentar uma LLM e persistência local em SQLite.

## Estrutura

```
centralos2/           # Pacote principal organizado em módulos
├── asic.py          # Gestão da frota de ASICs via HTTP
├── automation.py    # Motor de regras de automação
├── ble.py           # Coleta de sensores BLE (Xiaomi/ATC)
├── config.py        # Modelo e carregamento da configuração (YAML)
├── database.py      # Camada de persistência SQLite
├── f2pool.py        # Cliente de API F2Pool
├── llm.py           # Ponte com provedores de LLM via logs
├── logging_utils.py # Configuração de logs rotativos
├── modbus.py        # Integrações Modbus TCP (inversor e ABB)
├── service.py       # Orquestração assíncrona do sistema
└── __main__.py      # Interface de linha de comando (`python -m centralos2`)
```

Arquivos de apoio:

- `centralos2.py`: *launcher* compatível com a versão legada.
- `centralos.yaml`: arquivo de configuração padrão (modifique conforme seu ambiente).
- `logs/` e `data/`: criados automaticamente para armazenar logs rotativos e banco SQLite.

## Requisitos

- Python 3.11+
- Dependências principais: `pymodbus`, `bleak`, `aiohttp`, `pyyaml`, `requests`, `openai` (opcional para a ponte LLM).

Utilize um *virtualenv* e instale as dependências conforme necessário:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # crie conforme sua distribuição
```

> **Nota:** O pacote detecta automaticamente a ausência de dependências opcionais (ex.: `bleak`, `openai`) e ajusta o comportamento com mensagens de log.

## Execução

1. Ajuste `centralos.yaml` com os endereços IP/hostnames dos dispositivos e parâmetros desejados.
2. Exporte a chave da API da OpenAI caso deseje habilitar a ponte de LLM:

   ```bash
   export OPENAI_API_KEY="sua-chave"
   ```

3. Execute o serviço:

   ```bash
   python centralos2.py --config centralos.yaml
   # ou
   python -m centralos2 --config centralos.yaml
   ```

Os logs rotativos serão gravados em `logs/centralos.log`. Eventos, métricas e interações com LLM são persistidos em `data/centralos.db`.

## Automação e LLM

- As regras de automação são definidas no bloco `automation.rules` do YAML e suportam as automações nativas descritas no script original (segurança do inversor, guardas de umidade e ponto de orvalho).
- A ponte com LLM lê trechos recentes do log, envia ao provedor configurado (OpenAI por padrão) e registra as respostas no banco.

## Desenvolvimento

- O código é organizado em módulos independentes para facilitar manutenção, testes e reutilização.
- Adapte `automation.py` para adicionar novas regras de negócio.
- Novos coletores podem ser adicionados replicando o padrão de `modbus.py` ou `ble.py`.

## Monitoramento

O serviço utiliza `logging` com `RotatingFileHandler`. Ajuste limites de tamanho/retenção no bloco `logging` do YAML.

## Licença

Distribuído conforme os termos definidos pelo autor original do script centralos2.
