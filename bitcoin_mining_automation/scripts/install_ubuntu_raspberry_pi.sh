#!/bin/bash

# Script de instalação para Raspberry Pi com Ubuntu
# Sistema de Automação para Mineração de Bitcoin
# Compatível com Ubuntu 20.04+, 22.04+, 24.04+ e 25.x

set -e

echo "🚀 Instalando Sistema de Automação para Mineração de Bitcoin no Raspberry Pi (Ubuntu)"
echo "Versão: Ubuntu 20.04+ / 22.04+ / 24.04+ / 25.x"
echo "Arquitetura: ARM64/ARMHF"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    error "Por favor, execute como root (sudo ./install_ubuntu_raspberry_pi.sh)"
fi

# Verificar distribuição
if ! grep -q "Ubuntu" /etc/os-release; then
    error "Este script é específico para Ubuntu. Distribuição detectada: $(cat /etc/os-release | grep PRETTY_NAME)"
fi

# Verificar versão do Ubuntu
UBUNTU_VERSION=$(lsb_release -rs)
UBUNTU_CODENAME=$(lsb_release -cs)
log "Versão do Ubuntu detectada: $UBUNTU_VERSION ($UBUNTU_CODENAME)"

if [[ "$UBUNTU_VERSION" < "20.04" ]]; then
    error "Ubuntu 20.04+ é necessário. Versão atual: $UBUNTU_VERSION"
fi

# Verificar arquitetura
ARCH=$(uname -m)
log "Arquitetura detectada: $ARCH"

if [[ "$ARCH" != "aarch64" && "$ARCH" != "armv7l" ]]; then
    warn "Arquitetura não detectada como ARM. Continuando mesmo assim..."
fi

# Determinar usuário alvo para permissões e serviços
TARGET_USER=${SUDO_USER:-$(id -un)}
log "Usuário alvo para instalação: $TARGET_USER"

# Atualizar sistema
log "Atualizando sistema Ubuntu..."
apt-get update
apt-get upgrade -y

# Instalar dependências básicas
log "Instalando dependências básicas..."
apt-get install -y \
    curl \
    wget \
    git \
    rsync \
    vim \
    htop \
    tree \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    cmake \
    pkg-config \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-tk \
    python3-pil \
    python3-pil.imagetk

# Função para comparar versões (utiliza dpkg se disponível)
version_ge() {
    if command -v dpkg &> /dev/null; then
        dpkg --compare-versions "$1" ge "$2"
        return $?
    fi

    # Fallback simples: compara partes numéricas
    local IFS=.
    local i ver1=($1) ver2=($2)
    # preenche com zeros para o mesmo tamanho
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=${#ver2[@]}; i<${#ver1[@]}; i++)); do
        ver2[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++)); do
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 0
        elif ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 1
        fi
    done
    return 0
}

# Instalar Python 3.11+ (se necessário)
REQUIRED_PYTHON_VERSION="3.11"
CURRENT_PYTHON_VERSION="0"
if command -v python3 &> /dev/null; then
    CURRENT_PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
fi

if command -v python3 &> /dev/null && version_ge "$CURRENT_PYTHON_VERSION" "$REQUIRED_PYTHON_VERSION"; then
    log "Python $CURRENT_PYTHON_VERSION já instalado e compatível"
else
    log "Python compatível não encontrado. Instalando dependências..."
    case "$UBUNTU_VERSION" in
        20.04|20.10|21.*|22.*)
            log "Ubuntu $UBUNTU_VERSION detectado - utilizando PPA deadsnakes para Python 3.11"
            apt-get install -y software-properties-common
            add-apt-repository ppa:deadsnakes/ppa -y
            apt-get update
            apt-get install -y python3.11 python3.11-dev python3.11-venv python3.11-distutils
            update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
            ;;
        24.*|25.*)
            log "Ubuntu $UBUNTU_VERSION detectado - utilizando Python nativo (3.12+)"
            PYTHON_NATIVE_INSTALLED=false
            for candidate in 3.13 3.12; do
                if apt-cache show "python${candidate}" &> /dev/null; then
                    apt-get install -y "python${candidate}" "python${candidate}-dev" "python${candidate}-venv"
                    if apt-cache show "python${candidate}-distutils" &> /dev/null; then
                        apt-get install -y "python${candidate}-distutils"
                    fi
                    update-alternatives --install /usr/bin/python3 python3 "/usr/bin/python${candidate}" 1
                    PYTHON_NATIVE_INSTALLED=true
                    break
                fi
            done
            if [ "$PYTHON_NATIVE_INSTALLED" = false ]; then
                warn "Pacotes python3.12+ não disponíveis nos repositórios. Usando python3 padrão."
                apt-get install -y python3 python3-dev python3-venv
            else
                log "Python nativo instalado com sucesso"
            fi
            ;;
        *)
            warn "Versão do Ubuntu não reconhecida. Tentando instalar Python 3 padrão."
            apt-get install -y python3 python3-dev python3-venv
            ;;
    esac
    CURRENT_PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log "Python atualizado para $CURRENT_PYTHON_VERSION"
fi

# Garantir pacotes essenciais do Python
log "Garantindo pacotes Python essenciais..."
PYTHON_COMMON_PACKAGES=(python3 python3-dev python3-venv python3-pip python3-distutils)
for pkg in "${PYTHON_COMMON_PACKAGES[@]}"; do
    if apt-cache show "$pkg" &> /dev/null; then
        apt-get install -y "$pkg"
    else
        warn "Pacote $pkg não disponível para esta versão do Ubuntu"
    fi
done

# Instalar dependências para Modbus
log "Instalando dependências para Modbus..."
apt-get install -y \
    libmodbus-dev \
    pkg-config \
    libffi-dev \
    libssl-dev

# Instalar dependências para BLE
log "Instalando dependências para BLE..."
apt-get install -y \
    bluez \
    bluez-tools \
    libbluetooth-dev \
    libdbus-1-dev \
    libglib2.0-dev \
    libical-dev \
    libreadline-dev \
    libudev-dev

# Instalar dependências para processamento de dados
log "Instalando dependências para processamento de dados..."
apt-get install -y \
    libhdf5-dev \
    libhdf5-serial-dev \
    libatlas-base-dev \
    liblapack-dev \
    gfortran \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev

# Instalar dependências para interface gráfica
log "Instalando dependências para interface gráfica..."
apt-get install -y \
    xvfb \
    x11-utils \
    x11-xserver-utils \
    libxss1 \
    libgconf-2-4 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0

# Instalar Docker
log "Instalando Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Adicionar usuário ao grupo docker
usermod -aG docker "$TARGET_USER"

# Instalar Docker Compose
log "Instalando Docker Compose..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verificar instalação do Docker
log "Verificando instalação do Docker..."
docker --version
docker-compose --version

# Instalar Node.js (para frontend)
log "Instalando Node.js..."
if command -v node &> /dev/null; then
    log "Node.js já instalado (versão $(node --version))"
else
    NODE_MAJOR=20
    NODESOURCE_RELEASE_URL="https://deb.nodesource.com/node_${NODE_MAJOR}.x/dists/${UBUNTU_CODENAME}/Release"
    if curl -fsI "$NODESOURCE_RELEASE_URL" >/dev/null 2>&1; then
        log "Distribuição suportada pela NodeSource. Instalando Node.js ${NODE_MAJOR}.x via repositório oficial"
        curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash -
        apt-get install -y nodejs
    else
        warn "NodeSource ainda não suporta o codinome ${UBUNTU_CODENAME}. Utilizando pacotes do Ubuntu"
        apt-get install -y nodejs npm
    fi
fi

# Instalar Yarn (se npm estiver disponível)
if command -v npm &> /dev/null; then
    npm install -g yarn
else
    warn "npm não encontrado; Yarn não será instalado automaticamente"
fi

# Criar diretórios
log "Criando diretórios..."
mkdir -p /opt/bitcoin_mining
mkdir -p /opt/bitcoin_mining/data
mkdir -p /opt/bitcoin_mining/logs
mkdir -p /opt/bitcoin_mining/backup
mkdir -p /opt/bitcoin_mining/config
mkdir -p /opt/bitcoin_mining/reports
mkdir -p /opt/bitcoin_mining/logs_csv

# Copiar código do repositório ou baixar pacote oficial
log "Atualizando conteúdo em /opt/bitcoin_mining..."
SOURCE_DIR="$(pwd)"
OFFICIAL_PACKAGE_URL="${OFFICIAL_PACKAGE_URL:-https://github.com/centralos/bitcoin_mining_automation/archive/refs/heads/main.tar.gz}"

if [ -f "$SOURCE_DIR/docker-compose.yml" ] && [ -d "$SOURCE_DIR/backend" ] && [ -f "$SOURCE_DIR/.env.example" ]; then
    log "Copiando arquivos do repositório atual para /opt/bitcoin_mining"
    rsync -a --delete --exclude '.git' --exclude '.venv' --exclude 'node_modules' "$SOURCE_DIR/" /opt/bitcoin_mining/
else
    warn "Repositório atual não contém os arquivos esperados. Baixando pacote oficial..."
    TEMP_DIR="$(mktemp -d)"
    if curl -fsSL "$OFFICIAL_PACKAGE_URL" -o "$TEMP_DIR/package.tar.gz"; then
        tar -xzf "$TEMP_DIR/package.tar.gz" -C "$TEMP_DIR"
        SOURCE_EXTRACT=$(find "$TEMP_DIR" -maxdepth 1 -mindepth 1 -type d | head -n 1)
        if [ -n "$SOURCE_EXTRACT" ]; then
            rsync -a --delete "$SOURCE_EXTRACT/" /opt/bitcoin_mining/
        else
            rm -rf "$TEMP_DIR"
            error "Falha ao localizar diretório dentro do pacote oficial."
        fi
    else
        rm -rf "$TEMP_DIR"
        error "Não foi possível baixar o pacote oficial a partir de $OFFICIAL_PACKAGE_URL."
    fi
    rm -rf "$TEMP_DIR"
fi

# Validar arquivos essenciais
if [ ! -f "/opt/bitcoin_mining/docker-compose.yml" ] || [ ! -d "/opt/bitcoin_mining/backend" ] || [ ! -f "/opt/bitcoin_mining/.env.example" ]; then
    error "Arquivos essenciais não encontrados em /opt/bitcoin_mining. Verifique a origem do repositório."
fi

# Configurar permissões
chown -R "$TARGET_USER":"$TARGET_USER" /opt/bitcoin_mining

# Instalar dependências Python específicas
log "Instalando dependências Python específicas..."
cd /opt/bitcoin_mining

# Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências Python
pip install --upgrade pip
pip install wheel setuptools

# Dependências básicas
pip install \
    fastapi \
    uvicorn \
    pydantic \
    sqlalchemy \
    psycopg2-binary \
    redis \
    pymodbus \
    requests \
    httpx \
    schedule \
    tenacity \
    pandas \
    numpy \
    matplotlib \
    seaborn \
    plotly

# Dependências para BLE
pip install \
    bleak \
    atc-mi-interface

# Dependências para interface gráfica
pip install \
    ttkbootstrap \
    pillow

# Dependências para processamento de dados
pip install \
    scikit-learn \
    scipy \
    opencv-python

# Dependências para monitoramento
pip install \
    prometheus-client \
    structlog \
    loguru

# Dependências para desenvolvimento
pip install \
    pytest \
    pytest-asyncio \
    black \
    isort \
    flake8

# Instalar HashCore Toolkit (se disponível)
log "Verificando HashCore Toolkit..."
if command -v hashcore &> /dev/null; then
    log "HashCore Toolkit já instalado"
else
    warn "HashCore Toolkit não encontrado. Instalando versão compatível..."
    
    # Tentar instalar via pip
    pip install hashcore-toolkit || {
        warn "HashCore Toolkit não disponível via pip. Instale manualmente:"
        info "1. Baixe o arquivo .deb do site oficial"
        info "2. Execute: sudo dpkg -i hashcore-toolkit.deb"
        info "3. Execute: sudo apt-get install -f"
    }
fi

# Configurar sistema de inicialização
log "Configurando sistema de inicialização..."

# Criar serviço systemd
cat > /etc/systemd/system/bitcoin-mining.service << EOF
[Unit]
Description=Bitcoin Mining Automation System
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/bitcoin_mining
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=$TARGET_USER
Group=$TARGET_USER

[Install]
WantedBy=multi-user.target
EOF

# Criar serviço para o script Python (alternativo)
cat > /etc/systemd/system/bitcoin-mining-python.service << EOF
[Unit]
Description=Bitcoin Mining Automation System (Python)
After=network.target

[Service]
Type=simple
User=$TARGET_USER
Group=$TARGET_USER
WorkingDirectory=/opt/bitcoin_mining
Environment=PATH=/opt/bitcoin_mining/.venv/bin
ExecStart=/opt/bitcoin_mining/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Recarregar systemd
systemctl daemon-reload

# Habilitar serviços
systemctl enable bitcoin-mining.service
systemctl enable bitcoin-mining-python.service

# Configurar firewall (se ufw estiver instalado)
if command -v ufw &> /dev/null; then
    log "Configurando firewall..."
    ufw allow 8000/tcp  # API
    ufw allow 3000/tcp  # Frontend
    ufw allow 3001/tcp  # Grafana
    ufw allow 9090/tcp  # Prometheus
    ufw allow 15672/tcp # RabbitMQ Management
    ufw allow 502/tcp   # Modbus TCP
    ufw allow 503/tcp   # Modbus TCP (ABB)
fi

# Configurar swap (se necessário)
log "Verificando configuração de swap..."
if [ $(swapon --show | wc -l) -eq 0 ]; then
    warn "Nenhum swap configurado. Recomendado para sistemas com pouca RAM."
    read -p "Deseja configurar swap? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Configurando swap de 2GB..."
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
fi

# Configurar limite de arquivos
log "Configurando limite de arquivos..."
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Configurar kernel parameters
log "Configurando parâmetros do kernel..."
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
echo "net.core.somaxconn=65535" >> /etc/sysctl.conf
echo "net.core.netdev_max_backlog=5000" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog=4096" >> /etc/sysctl.conf
sysctl -p

# Configurar GPIO (se disponível)
log "Configurando GPIO..."
if [ -d "/sys/class/gpio" ]; then
    info "GPIO disponível - configurando permissões"
    echo "SUBSYSTEM==\"gpio\", GROUP=\"gpio\", MODE=\"0664\"" > /etc/udev/rules.d/99-gpio.rules
    echo "SUBSYSTEM==\"gpio\", KERNEL==\"gpiochip*\", GROUP=\"gpio\", MODE=\"0664\"" >> /etc/udev/rules.d/99-gpio.rules
    udevadm control --reload-rules
    udevadm trigger
else
    warn "GPIO não disponível - funcionalidades de controle de ventiladores limitadas"
fi

# Configurar Bluetooth
log "Configurando Bluetooth..."
systemctl enable bluetooth
systemctl start bluetooth

# Configurar permissões para Bluetooth
usermod -aG bluetooth "$TARGET_USER"

# Criar script de backup aprimorado
log "Criando script de backup aprimorado..."
cat > /opt/bitcoin_mining/backup.sh << 'EOF'
#!/bin/bash
# Script de backup aprimorado do sistema de mineração

BACKUP_DIR="/opt/bitcoin_mining/backup"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="bitcoin_mining_backup_$DATE.tar.gz"

echo "Criando backup: $BACKUP_FILE"

# Parar serviços
systemctl stop bitcoin-mining-python.service
docker-compose down

# Criar backup
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='backup' \
    --exclude='logs' \
    --exclude='data' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    .

# Reiniciar serviços
systemctl start bitcoin-mining-python.service
docker-compose up -d

echo "Backup criado: $BACKUP_DIR/$BACKUP_FILE"

# Limpar backups antigos (manter apenas os últimos 7)
cd "$BACKUP_DIR"
ls -t bitcoin_mining_backup_*.tar.gz | tail -n +8 | xargs -r rm

echo "Backup concluído e limpeza realizada"
EOF

chmod +x /opt/bitcoin_mining/backup.sh

# Criar script de monitoramento aprimorado
log "Criando script de monitoramento aprimorado..."
cat > /opt/bitcoin_mining/monitor.sh << 'EOF'
#!/bin/bash
# Script de monitoramento aprimorado do sistema

echo "=== Status do Sistema de Mineração ==="
echo "Data: $(date)"
echo

echo "=== Serviços do Sistema ==="
systemctl status bitcoin-mining-python.service --no-pager -l
echo

echo "=== Docker Containers ==="
docker-compose ps
echo

echo "=== Uso de Disco ==="
df -h
echo

echo "=== Uso de Memória ==="
free -h
echo

echo "=== Uso de CPU ==="
top -bn1 | grep "Cpu(s)"
echo

echo "=== Temperatura do Sistema =="
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    temp=$(cat /sys/class/thermal/thermal_zone0/temp)
    temp_c=$((temp/1000))
    echo "Temperatura da CPU: ${temp_c}°C"
fi
echo

echo "=== Logs Recentes ==="
tail -20 /opt/bitcoin_mining/logs/bitcoin_mining.log 2>/dev/null || echo "Nenhum log encontrado"
echo

echo "=== Estatísticas de Rede ==="
ss -tuln | grep -E ":(8000|3000|3001|9090|15672|502|503)"
echo

echo "=== Status dos Sensores BLE ==="
if command -v bluetoothctl &> /dev/null; then
    bluetoothctl show | grep "Powered"
    bluetoothctl devices | wc -l | xargs echo "Dispositivos BLE encontrados:"
fi
EOF

chmod +x /opt/bitcoin_mining/monitor.sh

# Criar script de atualização aprimorado
log "Criando script de atualização aprimorado..."
cat > /opt/bitcoin_mining/update.sh << 'EOF'
#!/bin/bash
# Script de atualização aprimorado do sistema

echo "Atualizando sistema de mineração..."

# Fazer backup
./backup.sh

# Parar serviços
systemctl stop bitcoin-mining-python.service
docker-compose down

# Atualizar código (se for um repositório git)
if [ -d ".git" ]; then
    git pull
fi

# Atualizar dependências Python
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Atualizar dependências Node.js
if [ -f "package.json" ]; then
    npm install
    yarn install
fi

# Reconstruir e reiniciar
docker-compose up -d --build
systemctl start bitcoin-mining-python.service

echo "Sistema atualizado com sucesso!"
EOF

chmod +x /opt/bitcoin_mining/update.sh

# Criar script de diagnóstico
log "Criando script de diagnóstico..."
cat > /opt/bitcoin_mining/diagnose.sh << 'EOF'
#!/bin/bash
# Script de diagnóstico do sistema

echo "=== Diagnóstico do Sistema de Mineração ==="
echo "Data: $(date)"
echo

echo "=== Verificação de Dependências ==="
echo "Python 3: $(python3 --version 2>/dev/null || echo 'NÃO INSTALADO')"
echo "Docker: $(docker --version 2>/dev/null || echo 'NÃO INSTALADO')"
echo "Docker Compose: $(docker-compose --version 2>/dev/null || echo 'NÃO INSTALADO')"
echo "Node.js: $(node --version 2>/dev/null || echo 'NÃO INSTALADO')"
echo "HashCore: $(hashcore --version 2>/dev/null || echo 'NÃO INSTALADO')"
echo

echo "=== Verificação de Portas ==="
for port in 8000 3000 3001 9090 15672 502 503; do
    if ss -tuln | grep -q ":$port "; then
        echo "Porta $port: ABERTA"
    else
        echo "Porta $port: FECHADA"
    fi
done
echo

echo "=== Verificação de Arquivos ==="
for file in main.py docker-compose.yml requirements.txt; do
    if [ -f "$file" ]; then
        echo "$file: PRESENTE"
    else
        echo "$file: AUSENTE"
    fi
done
echo

echo "=== Verificação de Permissões ==="
if [ -w "/opt/bitcoin_mining" ]; then
    echo "Diretório principal: ESCREVÍVEL"
else
    echo "Diretório principal: NÃO ESCREVÍVEL"
fi
echo

echo "=== Verificação de Logs ==="
if [ -f "logs/bitcoin_mining.log" ]; then
    echo "Log principal: PRESENTE ($(wc -l < logs/bitcoin_mining.log) linhas)"
else
    echo "Log principal: AUSENTE"
fi
echo

echo "=== Verificação de Configuração ==="
if [ -f ".env" ]; then
    echo "Arquivo .env: PRESENTE"
else
    echo "Arquivo .env: AUSENTE (copie de env.example)"
fi
echo

echo "=== Verificação de Rede ==="
ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo "Conectividade: OK" || echo "Conectividade: FALHA"
echo

echo "=== Verificação de GPIO ==="
if [ -d "/sys/class/gpio" ]; then
    echo "GPIO: DISPONÍVEL"
else
    echo "GPIO: NÃO DISPONÍVEL"
fi
echo

echo "=== Verificação de BLE ==="
if command -v bluetoothctl &> /dev/null; then
    bluetoothctl show | grep -q "Powered: yes" && echo "Bluetooth: ATIVO" || echo "Bluetooth: INATIVO"
else
    echo "Bluetooth: NÃO INSTALADO"
fi
EOF

chmod +x /opt/bitcoin_mining/diagnose.sh

# Configurar cron para backup automático
log "Configurando backup automático..."
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/bitcoin_mining/backup.sh") | crontab -

# Configurar cron para limpeza de logs
(crontab -l 2>/dev/null; echo "0 3 * * 0 find /opt/bitcoin_mining/logs -name '*.log' -mtime +7 -delete") | crontab -

# Configurar cron para limpeza de dados antigos
(crontab -l 2>/dev/null; echo "0 4 * * 0 find /opt/bitcoin_mining/logs_csv -name '*.csv' -mtime +30 -delete") | crontab -

# Criar arquivo .env de exemplo aprimorado
log "Criando arquivo .env de exemplo aprimorado..."
cat > /opt/bitcoin_mining/.env.example << 'EOF'
# Configurações do Sistema de Automação para Mineração de Bitcoin
# Configurado automaticamente para Raspberry Pi com Ubuntu

# =============================================================================
# CONFIGURAÇÕES GERAIS
# =============================================================================
DEBUG=false
LOG_LEVEL=INFO
APP_NAME="Bitcoin Mining Automation"
APP_VERSION="1.0.0"

# =============================================================================
# BANCO DE DADOS
# =============================================================================
DATABASE_URL=postgresql://bitcoin_mining:password@localhost:5432/bitcoin_mining
REDIS_URL=redis://localhost:6379

# =============================================================================
# MESSAGE QUEUE
# =============================================================================
RABBITMQ_URL=amqp://guest:guest@localhost:5672

# =============================================================================
# LLM (LARGE LANGUAGE MODEL)
# =============================================================================
LLM_MODE=local
LLM_ENDPOINT=http://localhost:11434

# =============================================================================
# DISPOSITIVOS
# =============================================================================
# Inversor ABB
ABB_HOST=192.168.0.111
ABB_PORT=502
ABB_SLAVE_ID=1

# Multimedidor ABB
ABB_SENSOR_IP=192.168.0.108
ABB_SENSOR_PORT=503

# Sensores BLE
BLE_INTERFACE=/dev/ttyUSB0
BLE_BAUDRATE=9600

# ASICs
HASHCORE_PATH=/usr/local/bin/hashcore
ASIC_TIMEOUT=30
ASIC_RETRY_ATTEMPTS=3

# =============================================================================
# POOLS DE MINERAÇÃO
# =============================================================================
F2POOL_API_TOKEN=your_f2pool_api_token_here
POOL_URL=https://api.f2pool.com
MINING_USER_NAME=USER
CURRENCY=BTC

# =============================================================================
# NOTIFICAÇÕES
# =============================================================================
WHATSAPP_TOKEN=your_whatsapp_business_token_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password_here

# =============================================================================
# CONFIGURAÇÕES DE SEGURANÇA
# =============================================================================
HUMIDITY_CRITICAL=90.0
DEW_POINT_DIFF_CRITICAL=4.0
INVERTER_NOT_RUN_TIMEOUT=30
CONNECTION_TIMEOUT=30
FAN_SPEED_HUMIDITY=20
FAN_SPEED_DEW_POINT=10

# =============================================================================
# CONFIGURAÇÕES ESPECÍFICAS DO RASPBERRY PI
# =============================================================================
FAN_GPIO_PIN=18
COOLING_GPIO_PIN=19
SWAP_SIZE=2G

# =============================================================================
# CONFIGURAÇÕES ESPECÍFICAS DO UBUNTU
# =============================================================================
DISPLAY=:0
XAUTHORITY=/home/$USER/.Xauthority
EOF

# Criar README aprimorado para o usuário
log "Criando documentação aprimorada..."
cat > /opt/bitcoin_mining/README_UBUNTU_RASPBERRY_PI.md << 'EOF'
# Sistema de Automação para Mineração de Bitcoin - Raspberry Pi (Ubuntu)

## Instalação Concluída

O sistema foi instalado com sucesso no seu Raspberry Pi com Ubuntu!

## Funcionalidades Implementadas

### ✅ Monitoramento em Tempo Real
- **Inversor/Exaustor**: Modbus TCP para controle de velocidade e status
- **Multimedidor ABB**: Leitura de tensão, corrente, potência e energia
- **ASICs**: Controle via HashCore Toolkit com sleep/resume
- **Sensores BLE**: Temperatura, umidade e ponto de orvalho (Xiaomi)
- **F2Pool**: Hashrate em tempo real e histórico

### ✅ Automação de Segurança
- **Inversor não em RUN**: Coloca ASICs em sleep automaticamente
- **Umidade ≥ 90%**: Ajusta ventilador para 20%
- **Diferença T-DP < 4°C**: Ajusta ventilador para 10%
- **Timeouts de conexão**: Alertas automáticos

### ✅ Sistema de Agendamento
- **Rotinas automáticas**: Sleep/resume de ASICs
- **Controle de ventiladores**: Ajustes baseados em horário
- **Alertas programados**: Notificações em horários específicos

### ✅ Relatórios e Logs
- **CSV automático**: Histórico de todos os dispositivos
- **Relatórios visuais**: Interface para visualização
- **Exportação**: CSV, JSON, Excel
- **Limpeza automática**: Dados antigos removidos automaticamente

### ✅ Interface Gráfica
- **Tkinter + ttkbootstrap**: Interface moderna e responsiva
- **Tema flatly**: Visual profissional
- **Canvas com scrollbar**: Suporte a muitos dispositivos
- **Menus organizados**: Acesso fácil a todas as funcionalidades

## Próximos Passos

### 1. Configurar Variáveis de Ambiente
```bash
cd /opt/bitcoin_mining
cp .env.example .env
nano .env
```

### 2. Configurar Dispositivos
```bash
# Editar configuração de dispositivos
nano config/devices.yaml
```

### 3. Iniciar o Sistema

#### Opção A: Docker (Recomendado)
```bash
docker-compose up -d
```

#### Opção B: Python Direto
```bash
source .venv/bin/activate
python main.py
```

#### Opção C: Serviço do Sistema
```bash
sudo systemctl start bitcoin-mining-python.service
```

### 4. Verificar Status
```bash
./monitor.sh
./diagnose.sh
```

## Acessar Interfaces

- **API**: http://seu-ip:8000
- **Frontend**: http://seu-ip:3000
- **Grafana**: http://seu-ip:3001
- **Prometheus**: http://seu-ip:9090
- **RabbitMQ Management**: http://seu-ip:15672

## Comandos Úteis

### Gerenciamento de Serviços
```bash
# Iniciar sistema
sudo systemctl start bitcoin-mining-python.service
docker-compose up -d

# Parar sistema
sudo systemctl stop bitcoin-mining-python.service
docker-compose down

# Ver status
sudo systemctl status bitcoin-mining-python.service
docker-compose ps
```

### Scripts de Manutenção
```bash
# Backup
./backup.sh

# Atualização
./update.sh

# Monitoramento
./monitor.sh

# Diagnóstico
./diagnose.sh
```

### Logs e Relatórios
```bash
# Ver logs em tempo real
tail -f logs/bitcoin_mining.log

# Ver relatórios disponíveis
ls -la reports/

# Exportar relatórios
python scripts/export_reports.py
```

## Configuração de Dispositivos

### Inversor ABB
- **IP**: 192.168.0.111
- **Porta**: 502
- **Registros**: Velocidade, frequência, corrente, temperatura

### Multimedidor ABB
- **IP**: 192.168.0.108
- **Porta**: 503
- **Registros**: Tensão, corrente, potência, energia

### Sensores BLE
- **Sensor 1**: A4:C1:38:30:26:23
- **Sensor 2**: A4:C1:38:65:D8:21
- **Dados**: Temperatura, umidade, ponto de orvalho

### ASICs
- **Descoberta automática**: Escaneamento de rede
- **Controle**: Sleep/resume via HashCore Toolkit
- **Monitoramento**: Status, hashrate, temperatura

## Monitoramento

### Métricas Principais
- **Hashrate Total**: Soma de todos os ASICs
- **Eficiência Energética**: Hashrate por Watt
- **Temperatura Média**: Controle térmico
- **Uptime**: Tempo de atividade
- **ROI**: Retorno sobre investimento

### Alertas Automáticos
- **Desconexão**: > 30 segundos sem resposta
- **Temperatura**: > 80°C
- **Umidade**: ≥ 90%
- **Ponto de Orvalho**: Diferença < 4°C
- **Eficiência**: < 80% do esperado

## Solução de Problemas

### Problemas Comuns

1. **Dispositivos não conectam**
   ```bash
   ./diagnose.sh
   # Verificar IPs e portas
   ```

2. **Sensores BLE não funcionam**
   ```bash
   sudo systemctl status bluetooth
   bluetoothctl power on
   bluetoothctl scan on
   ```

3. **ASICs não respondem**
   ```bash
   # Verificar HashCore Toolkit
   hashcore --version
   # Verificar rede
   ping IP_DO_ASIC
   ```

4. **Interface não carrega**
   ```bash
   # Verificar dependências
   pip list | grep ttkbootstrap
   # Verificar permissões
   ls -la /opt/bitcoin_mining
   ```

### Logs de Debug
```bash
# Ativar debug
export DEBUG=true
export LOG_LEVEL=DEBUG

# Ver logs detalhados
tail -f logs/bitcoin_mining.log
```

## Suporte

Para suporte, consulte:
- **Documentação**: /opt/bitcoin_mining/docs/
- **Logs**: /opt/bitcoin_mining/logs/
- **Relatórios**: /opt/bitcoin_mining/reports/
- **Configuração**: /opt/bitcoin_mining/config/

## Atualizações

O sistema suporta atualizações automáticas:
```bash
./update.sh
```

## Backup e Restauração

### Backup Automático
- **Frequência**: Diário às 2:00
- **Retenção**: 7 backups
- **Localização**: /opt/bitcoin_mining/backup/

### Backup Manual
```bash
./backup.sh
```

### Restauração
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

---

**Sistema instalado com sucesso!** 🎉

Todas as funcionalidades do seu script original foram implementadas e aprimoradas com:
- Arquitetura modular e escalável
- Interface gráfica moderna
- Sistema de logs robusto
- Automação de segurança
- Relatórios automáticos
- Monitoramento completo
- Fácil manutenção e atualização
EOF

# Finalizar instalação
log "Instalação concluída com sucesso!"
echo
echo "=========================================="
echo "🎉 Sistema instalado com sucesso!"
echo "=========================================="
echo
echo "Funcionalidades implementadas:"
echo "✅ Monitoramento em tempo real (Modbus, BLE, F2Pool)"
echo "✅ Controle de ASICs via HashCore Toolkit"
echo "✅ Automação de segurança inteligente"
echo "✅ Sistema de agendamento e rotinas"
echo "✅ Relatórios automáticos em CSV"
echo "✅ Interface gráfica moderna"
echo "✅ Sistema de logs robusto"
echo "✅ Monitoramento completo"
echo
echo "Próximos passos:"
echo "1. cd /opt/bitcoin_mining"
echo "2. cp .env.example .env"
echo "3. nano .env  # Configure suas variáveis"
echo "4. ./diagnose.sh  # Verificar sistema"
echo "5. docker-compose up -d  # Iniciar com Docker"
echo "6. ./monitor.sh  # Verificar status"
echo
echo "Acesse: http://$(hostname -I | awk '{print $1}'):8000"
echo
echo "Documentação: /opt/bitcoin_mining/README_UBUNTU_RASPBERRY_PI.md"
echo
log "Instalação finalizada!"
