# Revisão e Compatibilidade com Ubuntu ARM

## Visão Geral do Repositório

O projeto principal está no diretório `bitcoin_mining_automation/` e fornece um backend em FastAPI, scripts de instalação e monitoramento, além de orquestração via Docker Compose para a automação de uma infraestrutura de mineração de Bitcoin. A arquitetura técnica detalha a integração entre backend, coleta de dados (ABB, ASICs, BLE), notificações e monitoramento com Prometheus/Grafana.【F:bitcoin_mining_automation/docs/TECHNICAL_ARCHITECTURE.md†L1-L88】

Os scripts `install_linux.sh` e `quick_start_linux.sh` tratam da instalação universal em distribuições Linux e incluem suporte explícito a arquiteturas ARM (ARM64/ARMHF).【F:bitcoin_mining_automation/install_linux.sh†L9-L92】【F:bitcoin_mining_automation/quick_start_linux.sh†L1-L88】 Há, ainda, um script específico para Raspberry Pi com Ubuntu (`scripts/install_ubuntu_raspberry_pi.sh`) que automatiza a preparação da plataforma ARM, cobrindo dependências de Modbus, BLE e bibliotecas Python, além de ajustes relacionados ao HashCore Toolkit.【F:bitcoin_mining_automation/scripts/install_ubuntu_raspberry_pi.sh†L1-L214】【F:bitcoin_mining_automation/scripts/install_ubuntu_raspberry_pi.sh†L300-L372】

## Avaliação de Compatibilidade Ubuntu ARM

1. **Scripts de instalação** – O script dedicado ao Ubuntu em ARM verifica a arquitetura (`aarch64`/`armv7l`), instala dependências via `apt` (incluindo bibliotecas Modbus/BLE) e agora detecta automaticamente se o repositório da NodeSource suporta o codinome do Ubuntu, adotando o pacote nativo quando necessário. Isso confirma suporte direto a Ubuntu ARM a partir da versão 20.04.【F:bitcoin_mining_automation/scripts/install_ubuntu_raspberry_pi.sh†L25-L214】【F:bitcoin_mining_automation/scripts/install_ubuntu_raspberry_pi.sh†L215-L252】
2. **Backend/Docker** – O backend usa base `python:3.11-slim`, disponível em ARM, e instala bibliotecas Python compatíveis. O `docker-compose.yml` define `LLM_MODE` como desabilitado por padrão e expõe o serviço Ollama atrás de um profile opcional, evitando a tentativa de baixar imagens somente `amd64` em ARM.【F:bitcoin_mining_automation/docker-compose.yml†L7-L118】
3. **Frontend opcional** – O `docker-compose.yml` coloca o serviço `frontend` sob um profile específico. Assim, a execução padrão (`docker compose up`) funciona sem depender de um diretório inexistente, mantendo a possibilidade de habilitar o componente quando o código estiver disponível.【F:bitcoin_mining_automation/docker-compose.yml†L119-L146】
4. **HashCore Toolkit** – O backend e os scripts esperam o binário `hashcore` em `/usr/local/bin`. O guia de execução para Ubuntu ARM fornece um pacote `.deb` específico (`hashcore-toolkit_1.0.0_arm64.deb`); se o pacote não estiver disponível para a arquitetura utilizada, deve-se instalar via `pip install hashcore-toolkit`, sujeito à disponibilidade de wheels ARM.【F:bitcoin_mining_automation/GUIA_EXECUCAO_RASPBERRY_PI_UBUNTU.md†L249-L320】【F:bitcoin_mining_automation/backend/core/data_collectors/asic_collector.py†L28-L336】
5. **Dependências externas** – Os serviços PostgreSQL, Redis, RabbitMQ, Prometheus e Grafana utilizam imagens multi-arquitetura. Em Ubuntu ARM, o `docker compose` puxa as variantes ARM automaticamente, mantendo Ollama e o frontend como opt-in.【F:bitcoin_mining_automation/docker-compose.yml†L19-L146】
6. **Bibliotecas de IA** – As dependências pesadas (`torch`/`transformers`) foram movidas para um arquivo opcional (`backend/requirements-ml.txt`), evitando falhas de build em ARM quando esses componentes não são necessários.【F:bitcoin_mining_automation/backend/requirements.txt†L1-L53】【F:bitcoin_mining_automation/backend/requirements-ml.txt†L1-L9】

### Conclusão de Compatibilidade

- ✅ **Ubuntu ARM 20.04+ é suportado** pelos scripts e documentação do repositório.  
- ⚠️ **Serviço Ollama** continua opcional; habilite apenas se houver suporte à arquitetura e imagem disponível.
- ⚠️ **Serviço frontend** permanece opcional; forneça o código antes de habilitar o profile correspondente.
- ⚠️ **HashCore Toolkit** requer verificação manual para garantir a disponibilidade de pacotes/wheels ARM.  

## Passo a Passo para Instalação no Ubuntu ARM

A sequência abaixo pressupõe um Ubuntu ARM recém-instalado (por exemplo, Raspberry Pi 4 com Ubuntu Server 24.04) e acesso ao terminal com usuário com privilégios `sudo`.

```bash
# 1. Atualizar o sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependências básicas
sudo apt install -y curl wget git vim htop tree unzip \
    software-properties-common apt-transport-https ca-certificates gnupg lsb-release \
    build-essential cmake pkg-config python3 python3-dev python3-pip python3-venv \
    python3-tk python3-pil python3-pil.imagetk libmodbus-dev libffi-dev libssl-dev \
    bluez bluez-tools bluetooth

# 3. (Opcional) Configurar Python 3.11+ caso a versão padrão seja antiga
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-dev python3.11-venv python3.11-distutils
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 4. Clonar o repositório
cd /opt
sudo git clone https://github.com/seu-usuario/bitcoin-mining-automation.git
sudo chown -R $USER:$USER bitcoin-mining-automation
cd bitcoin-mining-automation

# 5. Copiar variáveis de ambiente e configurar
cp .env.example .env
nano .env

# 6. Ajustar configuração de dispositivos
mkdir -p config
nano config/devices.yaml

# 7. (Opcional) Instalar HashCore Toolkit para ARM64
wget https://releases.hashcore.io/hashcore-toolkit_1.0.0_arm64.deb
sudo dpkg -i hashcore-toolkit_1.0.0_arm64.deb || sudo apt -f install -y
# ou, se indisponível:
# pip install hashcore-toolkit

# 8. Instalar e habilitar Docker (necessário para stack completa)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
sudo systemctl enable docker

# 9. Instalar Docker Compose plugin
sudo apt install -y docker-compose-plugin

# 10. Subir os serviços essenciais
docker compose up -d

# 11. (Opcional) Habilitar serviços extras
# docker compose --profile ollama up -d    # Requer imagem amd64 do Ollama
# docker compose --profile frontend up -d  # Disponível após adicionar o código do frontend

# 12. Verificar status
docker compose ps

# 13. Acompanhar logs do backend
docker compose logs -f app
```

> 💡 Caso o Docker não seja necessário, é possível usar o script `scripts/install_ubuntu_raspberry_pi.sh` para instalar o backend e serviços diretamente no host, conforme descrito no `GUIA_EXECUCAO_RASPBERRY_PI_UBUNTU.md`.

## Recomendações Pós-Instalação

- Configure o firewall para liberar as portas 8000 (API), 3001 (Grafana), 5432 (PostgreSQL) e 6379 (Redis) conforme necessário.【F:bitcoin_mining_automation/GUIA_EXECUCAO_RASPBERRY_PI_UBUNTU.md†L199-L288】  
- Utilize os scripts de diagnóstico e monitoramento (`diagnose.sh`, `monitor.sh`) para validar o ambiente após a instalação.【F:bitcoin_mining_automation/GUIA_EXECUCAO_RASPBERRY_PI_UBUNTU.md†L129-L197】  
- Se optar pelo modo sem Docker, ajuste o serviço `bitcoin-mining-python.service` conforme indicado na documentação para inicialização automática.【F:bitcoin_mining_automation/GUIA_EXECUCAO_RASPBERRY_PI_UBUNTU.md†L97-L197】

