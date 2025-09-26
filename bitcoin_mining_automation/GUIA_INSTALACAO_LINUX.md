# Guia de Instalação - Linux Universal

## 📋 Pré-requisitos

### Hardware Mínimo
- **CPU**: 2 cores (recomendado: 4+ cores)
- **RAM**: 4GB (recomendado: 8GB+)
- **Disco**: 20GB livres (recomendado: 50GB+)
- **Rede**: Conexão estável com internet
- **Portas**: 8000, 3000, 3001, 9090, 15672, 502, 503

### Software Suportado
- **Ubuntu**: 20.04+, 22.04+, 24.04+, 25.x
- **Debian**: 10+, 11+
- **CentOS**: 7+, 8+
- **RHEL**: 7+, 8+
- **Fedora**: 35+
- **Arch Linux**: Rolling release
- **Outras distribuições**: Testadas e funcionais

### Arquiteturas Suportadas
- **x86_64** (AMD64)
- **ARM64** (AArch64)
- **ARMHF** (ARMv7)

## 🚀 Instalação Passo a Passo

### 1. Preparar o Sistema

#### 1.1 Atualizar o Sistema
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL/Fedora
sudo yum update -y
# ou
sudo dnf update -y

# Arch Linux
sudo pacman -Syu
```

#### 1.2 Instalar Dependências Básicas
```bash
# Ubuntu/Debian
sudo apt install -y curl wget git vim htop tree unzip

# CentOS/RHEL/Fedora
sudo yum install -y curl wget git vim htop tree unzip
# ou
sudo dnf install -y curl wget git vim htop tree unzip

# Arch Linux
sudo pacman -S curl wget git vim htop tree unzip
```

### 2. Baixar e Executar Instalação

#### 2.1 Baixar Script de Instalação
```bash
# Criar diretório temporário
mkdir -p ~/temp
cd ~/temp

# Baixar script de instalação
wget https://raw.githubusercontent.com/seu-usuario/bitcoin-mining-automation/main/install_linux.sh

# Tornar executável
chmod +x install_linux.sh
```

#### 2.2 Executar Instalação
```bash
# Executar como root
sudo ./install_linux.sh
```

**⏱️ Tempo estimado**: 20-45 minutos (dependendo da distribuição e velocidade da internet)

#### 2.3 Verificar Instalação
```bash
# Verificar se o diretório foi criado
ls -la /opt/bitcoin_mining

# Verificar dependências
/opt/bitcoin_mining/diagnose.sh
```

### 3. Configurar o Sistema

#### 3.1 Configurar Variáveis de Ambiente
```bash
# Navegar para o diretório
cd /opt/bitcoin_mining

# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

**Configurações importantes:**
```bash
# Configurações de rede
ABB_HOST=192.168.0.111          # IP do inversor ABB
ABB_SENSOR_IP=192.168.0.108     # IP do multimedidor ABB

# Configurações de pool
F2POOL_API_TOKEN=seu_token_aqui  # Token da F2Pool
MINING_USER_NAME=seu_usuario     # Usuário da pool

# Configurações de notificação
TELEGRAM_BOT_TOKEN=seu_bot_token # Token do bot Telegram
SMTP_USER=seu_email@gmail.com    # Email para notificações
```

#### 3.2 Configurar Dispositivos
```bash
# Criar diretório de configuração
mkdir -p config

# Editar configuração de dispositivos
nano config/devices.yaml
```

**Exemplo de configuração:**
```yaml
inverter:
  host: "192.168.0.111"
  port: 502
  slave_id: 1

multimedidor:
  host: "192.168.0.108"
  port: 503
  slave_id: 1

ble_sensors:
  sensor_1:
    mac: "A4:C1:38:30:26:23"
    name: "Sensor Sala 1"
  sensor_2:
    mac: "A4:C1:38:65:D8:21"
    name: "Sensor Sala 2"

asics:
  discovery:
    enabled: true
    network_range: "192.168.0.0/24"
```

### 4. Iniciar o Sistema

#### 4.1 Opção A: Docker (Recomendado)
```bash
# Navegar para o diretório
cd /opt/bitcoin_mining

# Iniciar com Docker
docker-compose up -d

# Verificar status
docker-compose ps
```

#### 4.2 Opção B: Python Direto
```bash
# Ativar ambiente virtual
cd /opt/bitcoin_mining
source .venv/bin/activate

# Executar sistema
python main.py
```

#### 4.3 Opção C: Serviço do Sistema
```bash
# Iniciar serviço
sudo systemctl start bitcoin-mining-python.service

# Verificar status
sudo systemctl status bitcoin-mining-python.service

# Habilitar inicialização automática
sudo systemctl enable bitcoin-mining-python.service
```

### 5. Verificar Funcionamento

#### 5.1 Verificar Status
```bash
# Script de monitoramento
./monitor.sh

# Script de diagnóstico
./diagnose.sh
```

#### 5.2 Acessar Interfaces
- **API**: http://seu-ip:8000
- **Frontend**: http://seu-ip:3000
- **Grafana**: http://seu-ip:3001
- **Prometheus**: http://seu-ip:9090

#### 5.3 Verificar Logs
```bash
# Logs em tempo real
tail -f logs/bitcoin_mining.log

# Logs de erro
tail -f logs/errors.log
```

## 🔧 Configuração Avançada

### 1. Configurar Rede para Dispositivos Modbus

#### 1.1 Configurar IP Estático
```bash
# Ubuntu/Debian - Netplan
sudo nano /etc/netplan/50-cloud-init.yaml
```

**Exemplo de configuração:**
```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 192.168.0.100/24
      gateway4: 192.168.0.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
```

```bash
# Aplicar configuração
sudo netplan apply
```

#### 1.2 Configurar Firewall
```bash
# Ubuntu/Debian - UFW
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 3001/tcp
sudo ufw allow 9090/tcp
sudo ufw allow 15672/tcp
sudo ufw allow 502/tcp
sudo ufw allow 503/tcp

# CentOS/RHEL/Fedora - FirewallD
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --permanent --add-port=3001/tcp
sudo firewall-cmd --permanent --add-port=9090/tcp
sudo firewall-cmd --permanent --add-port=15672/tcp
sudo firewall-cmd --permanent --add-port=502/tcp
sudo firewall-cmd --permanent --add-port=503/tcp
sudo firewall-cmd --reload
```

### 2. Configurar Bluetooth para Sensores BLE

#### 2.1 Verificar Bluetooth
```bash
# Verificar status
sudo systemctl status bluetooth

# Iniciar se necessário
sudo systemctl start bluetooth
sudo systemctl enable bluetooth
```

#### 2.2 Configurar Sensores
```bash
# Entrar no bluetoothctl
bluetoothctl

# Ligar Bluetooth
power on

# Iniciar descoberta
scan on

# Parar descoberta (após encontrar sensores)
scan off

# Sair
exit
```

### 3. Configurar HashCore Toolkit

#### 3.1 Instalar HashCore Toolkit
```bash
# Baixar arquivo .deb (Ubuntu/Debian)
wget https://releases.hashcore.io/hashcore-toolkit_1.0.0_amd64.deb
sudo dpkg -i hashcore-toolkit_1.0.0_amd64.deb
sudo apt-get install -f

# Ou via pip
pip install hashcore-toolkit
```

#### 3.2 Configurar ASICs
```bash
# Verificar instalação
hashcore --version

# Descobrir ASICs
hashcore discover

# Listar ASICs
hashcore list
```

### 4. Configurar Swap (Opcional)

#### 4.1 Verificar Swap Atual
```bash
swapon --show
free -h
```

#### 4.2 Criar Swap se Necessário
```bash
# Criar arquivo de swap
sudo fallocate -l 2G /swapfile

# Configurar permissões
sudo chmod 600 /swapfile

# Formatar como swap
sudo mkswap /swapfile

# Ativar swap
sudo swapon /swapfile

# Tornar permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 📊 Monitoramento e Manutenção

### 1. Scripts de Manutenção

#### 1.1 Backup Automático
```bash
# Executar backup manual
./backup.sh

# Verificar backups
ls -la backup/
```

#### 1.2 Monitoramento
```bash
# Status completo
./monitor.sh

# Diagnóstico
./diagnose.sh
```

### 2. Logs e Relatórios

#### 2.1 Visualizar Logs
```bash
# Logs em tempo real
tail -f logs/bitcoin_mining.log

# Logs de erro
tail -f logs/errors.log

# Logs por data
ls -la logs/
```

#### 2.2 Gerar Relatórios
```bash
# Executar script de relatórios
python scripts/generate_reports.py

# Ver relatórios
ls -la reports/
```

### 3. Solução de Problemas

#### 3.1 Problemas Comuns

**Dispositivos não conectam:**
```bash
# Verificar conectividade
ping 192.168.0.111

# Verificar portas
nmap -p 502 192.168.0.111
```

**Sensores BLE não funcionam:**
```bash
# Verificar Bluetooth
bluetoothctl show

# Reiniciar Bluetooth
sudo systemctl restart bluetooth
```

**ASICs não respondem:**
```bash
# Verificar HashCore
hashcore --version

# Testar conexão
hashcore ping IP_DO_ASIC
```

**Interface não carrega:**
```bash
# Verificar dependências
pip list | grep ttkbootstrap

# Reinstalar dependências
pip install -r requirements.txt
```

#### 3.2 Logs de Debug
```bash
# Ativar debug
export DEBUG=true
export LOG_LEVEL=DEBUG

# Reiniciar sistema
sudo systemctl restart bitcoin-mining-python.service

# Ver logs detalhados
tail -f logs/bitcoin_mining.log
```

## 🔄 Atualizações e Backup

### 1. Sistema de Backup

#### 1.1 Backup Automático
- **Frequência**: Diário às 2:00
- **Retenção**: 7 backups
- **Localização**: `/opt/bitcoin_mining/backup/`

#### 1.2 Backup Manual
```bash
# Executar backup
./backup.sh

# Verificar backup
ls -la backup/
```

#### 1.3 Restauração
```bash
# Parar sistema
sudo systemctl stop bitcoin-mining-python.service
docker-compose down

# Restaurar backup
tar -xzf backup/bitcoin_mining_backup_YYYYMMDD_HHMMSS.tar.gz

# Reiniciar sistema
sudo systemctl start bitcoin-mining-python.service
docker-compose up -d
```

### 2. Atualizações

#### 2.1 Atualização do Sistema
```bash
# Atualizar sistema operacional
sudo apt update && sudo apt upgrade -y
# ou
sudo yum update -y
# ou
sudo dnf update -y
# ou
sudo pacman -Syu
```

#### 2.2 Atualização da Aplicação
```bash
# Fazer backup
./backup.sh

# Parar sistema
sudo systemctl stop bitcoin-mining-python.service
docker-compose down

# Atualizar código
git pull

# Atualizar dependências
source .venv/bin/activate
pip install -r requirements.txt

# Reiniciar sistema
sudo systemctl start bitcoin-mining-python.service
docker-compose up -d
```

## 📱 Acesso Remoto

### 1. SSH
```bash
# Conectar via SSH
ssh usuario@IP_DO_SERVIDOR

# Executar comandos remotos
ssh usuario@IP_DO_SERVIDOR "./monitor.sh"
```

### 2. Interface Web
- **API**: http://IP_DO_SERVIDOR:8000
- **Frontend**: http://IP_DO_SERVIDOR:3000
- **Grafana**: http://IP_DO_SERVIDOR:3001

### 3. Monitoramento Remoto
```bash
# Script de monitoramento remoto
./monitor.sh --remote

# Enviar relatórios por email
python scripts/send_reports.py
```

## 🚨 Alertas e Notificações

### 1. Configurar Alertas
```bash
# Editar configuração de alertas
nano config/automation.yaml
```

### 2. Canais de Notificação
- **WhatsApp**: Configurar token de API
- **Telegram**: Configurar bot token
- **Email**: Configurar SMTP
- **SMS**: Configurar provedor

### 3. Testar Alertas
```bash
# Testar notificação
python scripts/test_notifications.py
```

## 📈 Performance e Otimização

### 1. Monitoramento de Performance
```bash
# Ver uso de recursos
htop

# Ver uso de disco
df -h

# Ver uso de memória
free -h
```

### 2. Otimizações
```bash
# Configurar swap
sudo swapon --show

# Otimizar banco de dados
python scripts/optimize_database.py

# Limpar logs antigos
python scripts/cleanup_logs.py
```

## 🔒 Segurança

### 1. Configurações de Segurança
```bash
# Configurar firewall
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 8000
sudo ufw allow 3000

# Configurar SSH
sudo nano /etc/ssh/sshd_config
```

### 2. Backup de Segurança
```bash
# Backup de configurações
tar -czf config_backup.tar.gz config/

# Backup de chaves
tar -czf keys_backup.tar.gz .env
```

## 🎯 Resumo de Comandos Essenciais

```bash
# Instalação
sudo ./install_linux.sh

# Configuração
cp .env.example .env
nano .env

# Inicialização
docker-compose up -d

# Monitoramento
./monitor.sh
./diagnose.sh

# Backup
./backup.sh

# Logs
tail -f logs/bitcoin_mining.log
```

## 📞 Suporte

### Documentação
- **README**: `/opt/bitcoin_mining/README_LINUX.md`
- **Logs**: `/opt/bitcoin_mining/logs/`
- **Configuração**: `/opt/bitcoin_mining/config/`

### Comandos de Diagnóstico
```bash
# Diagnóstico completo
./diagnose.sh

# Verificar dependências
python -c "import fastapi, uvicorn, pydantic; print('Dependências OK')"

# Verificar serviços
systemctl status bitcoin-mining-python.service
docker-compose ps
```

---

**Sistema pronto para uso!** 🎉

Para suporte adicional, consulte a documentação em `/opt/bitcoin_mining/docs/` ou os logs em `/opt/bitcoin_mining/logs/`.
