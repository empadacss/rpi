# Guia de Execução - Raspberry Pi com Ubuntu

## 📋 Pré-requisitos

### Hardware
- **Raspberry Pi 4** (recomendado) ou Raspberry Pi 3B+
- **MicroSD** de 32GB+ (Classe 10 ou superior)
- **Fonte de alimentação** 5V/3A (oficial recomendada)
- **Cabo Ethernet** ou conexão Wi-Fi
- **Teclado e mouse** (para configuração inicial)

### Software
- **Ubuntu 20.04+** ou **Ubuntu 22.04+** para Raspberry Pi
- **Conexão com internet** estável
- **Acesso SSH** (opcional, mas recomendado)

## 🚀 Instalação Passo a Passo

### 1. Preparar o Raspberry Pi

#### 1.1 Instalar Ubuntu
1. Baixe a imagem do Ubuntu para Raspberry Pi:
   - [Ubuntu 22.04 LTS](https://ubuntu.com/download/raspberry-pi)
   - [Ubuntu 20.04 LTS](https://ubuntu.com/download/raspberry-pi)

2. Grave a imagem no microSD usando:
   - **Raspberry Pi Imager** (recomendado)
   - **Balena Etcher**
   - **dd** (Linux/macOS)

3. Configure o Wi-Fi (opcional):
   - Edite o arquivo `network-config` na partição `system-boot`
   - Ou configure após a primeira inicialização

#### 1.2 Primeira Inicialização
1. Insira o microSD no Raspberry Pi
2. Conecte a fonte de alimentação
3. Aguarde a inicialização (pode levar alguns minutos)
4. Faça login com as credenciais padrão:
   - **Usuário**: ubuntu
   - **Senha**: ubuntu (será solicitada para alterar)

#### 1.3 Configuração Inicial
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Configurar hostname
sudo hostnamectl set-hostname bitcoin-mining

# Configurar timezone
sudo timedatectl set-timezone America/Sao_Paulo

# Reiniciar
sudo reboot
```

### 2. Instalar o Sistema de Mineração

#### 2.1 Baixar o Script de Instalação
```bash
# Criar diretório temporário
mkdir -p ~/temp
cd ~/temp

# Baixar script de instalação
wget https://raw.githubusercontent.com/seu-usuario/bitcoin-mining-automation/main/scripts/install_ubuntu_raspberry_pi.sh

# Tornar executável
chmod +x install_ubuntu_raspberry_pi.sh
```

#### 2.2 Executar Instalação
```bash
# Executar como root
sudo ./install_ubuntu_raspberry_pi.sh
```

**⏱️ Tempo estimado**: 15-30 minutos

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

#### 3.2 Configurar Dispositivos
```bash
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

### 1. Configurar GPIO para Controle de Ventiladores

#### 1.1 Habilitar GPIO
```bash
# Verificar se GPIO está disponível
ls -la /sys/class/gpio

# Configurar permissões
sudo usermod -a -G gpio ubuntu
```

#### 1.2 Testar GPIO
```bash
# Exportar pino
echo 18 > /sys/class/gpio/export

# Configurar como saída
echo out > /sys/class/gpio/gpio18/direction

# Testar (ligar)
echo 1 > /sys/class/gpio/gpio18/value

# Testar (desligar)
echo 0 > /sys/class/gpio/gpio18/value

# Unexportar
echo 18 > /sys/class/gpio/unexport
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

### 3. Configurar Rede para Dispositivos Modbus

#### 3.1 Configurar IP Estático
```bash
# Editar configuração de rede
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

#### 3.2 Aplicar Configuração
```bash
# Aplicar configuração
sudo netplan apply

# Verificar
ip addr show
```

### 4. Configurar HashCore Toolkit

#### 4.1 Instalar HashCore Toolkit
```bash
# Baixar arquivo .deb
wget https://releases.hashcore.io/hashcore-toolkit_1.0.0_arm64.deb

# Instalar
sudo dpkg -i hashcore-toolkit_1.0.0_arm64.deb

# Corrigir dependências se necessário
sudo apt-get install -f
```

#### 4.2 Configurar ASICs
```bash
# Verificar instalação
hashcore --version

# Descobrir ASICs
hashcore discover

# Listar ASICs
hashcore list
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

#### 1.2 Atualização do Sistema
```bash
# Atualizar sistema
./update.sh

# Verificar versão
cat VERSION
```

#### 1.3 Monitoramento
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

#### 2.1 Atualização Automática
```bash
# Verificar atualizações
./update.sh --check-only

# Atualizar sistema
./update.sh
```

#### 2.2 Atualização Manual
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
ssh ubuntu@IP_DO_RASPBERRY_PI

# Executar comandos remotos
ssh ubuntu@IP_DO_RASPBERRY_PI "./monitor.sh"
```

### 2. Interface Web
- **API**: http://IP_DO_RASPBERRY_PI:8000
- **Frontend**: http://IP_DO_RASPBERRY_PI:3000
- **Grafana**: http://IP_DO_RASPBERRY_PI:3001

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

---

## 🎯 Resumo de Comandos Essenciais

```bash
# Instalação
sudo ./install_ubuntu_raspberry_pi.sh

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

# Atualização
./update.sh

# Logs
tail -f logs/bitcoin_mining.log
```

**Sistema pronto para uso!** 🎉

Para suporte adicional, consulte a documentação em `/opt/bitcoin_mining/docs/` ou os logs em `/opt/bitcoin_mining/logs/`.
