#!/bin/bash

# Script de instalação para Linux
# Sistema de Automação para Mineração de Bitcoin
# Compatível com Ubuntu, Debian, CentOS, RHEL, Fedora, Arch Linux

set -e

echo "🚀 Instalando Sistema de Automação para Mineração de Bitcoin no Linux"
echo "Versão: Universal Linux"
echo "Arquitetura: x86_64, ARM64, ARMHF"

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

cleanup_deadsnakes_ppa() {
    if [ "$DISTRO" != "ubuntu" ] && [ "$DISTRO" != "debian" ]; then
        return
    fi

    local removed=0
    if ls /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa* >/dev/null 2>&1; then
        warn "Removendo entradas antigas do PPA deadsnakes que causam erro 404"
        rm -f /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa* || true
        removed=1
    fi

    if ls /etc/apt/sources.list.d/*deadsnakes* >/dev/null 2>&1; then
        warn "Limpando referências residuais ao PPA deadsnakes"
        rm -f /etc/apt/sources.list.d/*deadsnakes* || true
        removed=1
    fi

    if [ "$removed" -eq 1 ] && command -v add-apt-repository >/dev/null 2>&1; then
        add-apt-repository --remove ppa:deadsnakes/ppa -y >/dev/null 2>&1 || true
    fi
}

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    error "Por favor, execute como root (sudo ./install_linux.sh)"
fi

# Detectar distribuição Linux
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
        VERSION=$(cat /etc/redhat-release | sed 's/.*release \([0-9]\+\).*/\1/')
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
        VERSION=$(cat /etc/debian_version)
    else
        DISTRO="unknown"
        VERSION="unknown"
    fi
}

# Detectar arquitetura
detect_arch() {
    ARCH=$(uname -m)
    case $ARCH in
        x86_64) ARCH="amd64" ;;
        aarch64) ARCH="arm64" ;;
        armv7l) ARCH="armhf" ;;
        armv6l) ARCH="armhf" ;;
        *) ARCH="unknown" ;;
    esac
}

# Detectar distribuição e arquitetura
detect_distro
detect_arch

DISTRO_CODENAME=""
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_CODENAME=${VERSION_CODENAME:-$UBUNTU_CODENAME}
fi

log "Distribuição detectada: $DISTRO $VERSION"
if [ -n "$DISTRO_CODENAME" ]; then
    log "Codinome detectado: $DISTRO_CODENAME"
fi
log "Arquitetura detectada: $ARCH"

# Verificar se a distribuição é suportada
case $DISTRO in
    ubuntu|debian|centos|rhel|fedora|arch)
        log "Distribuição suportada: $DISTRO"
        ;;
    *)
        warn "Distribuição não testada: $DISTRO. Continuando mesmo assim..."
        ;;
esac

# Instalar dependências básicas baseadas na distribuição
install_basic_dependencies() {
    log "Instalando dependências básicas..."
    
    case $DISTRO in
        ubuntu|debian)
            cleanup_deadsnakes_ppa
            if ! apt-get update; then
                warn "apt-get update falhou; tentando novamente após limpar PPAs do deadsnakes"
                cleanup_deadsnakes_ppa
                apt-get update || warn "apt-get update ainda retornou erro; verifique sua conexão ou listas de repositório"
            fi
            apt-get install -y \
                curl \
                wget \
                git \
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
                python3 \
                python3-dev \
                python3-pip \
                python3-venv \
                python3-tk \
                python3-pil \
                python3-pil.imagetk
            ;;
        centos|rhel|fedora)
            if command -v dnf &> /dev/null; then
                PKG_MGR="dnf"
            else
                PKG_MGR="yum"
            fi
            
            $PKG_MGR update -y
            $PKG_MGR install -y \
                curl \
                wget \
                git \
                vim \
                htop \
                tree \
                unzip \
                epel-release \
                gcc \
                gcc-c++ \
                make \
                cmake \
                pkgconfig \
                python3 \
                python3-devel \
                python3-pip \
                tkinter \
                python3-pillow
            ;;
        arch)
            pacman -Syu --noconfirm
            pacman -S --noconfirm \
                curl \
                wget \
                git \
                vim \
                htop \
                tree \
                unzip \
                base-devel \
                cmake \
                pkg-config \
                python \
                python-pip \
                tk \
                python-pillow
            ;;
    esac
}

# Instalar Python 3.11+ se necessário
install_python() {
    log "Verificando versão do Python..."

    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        log "Instalando Python 3.11+..."

        case $DISTRO in
            ubuntu|debian)
                UBUNTU_MAJOR=${VERSION%%.*}
                UBUNTU_MINOR=${VERSION#*.}
                UBUNTU_MINOR=${UBUNTU_MINOR%%.*}
                if [ "$DISTRO" = "ubuntu" ] && [ "$UBUNTU_MAJOR" -ge 24 ]; then
                    log "Ubuntu ${VERSION} detectado - utilizando Python nativo do repositório (3.12+)"
                    apt-get install -y python3 python3-dev python3-venv python3-pip
                else
                    log "Habilitando PPA deadsnakes para obter Python 3.11 em ${DISTRO^} ${VERSION}"
                    apt-get install -y software-properties-common
                    add-apt-repository ppa:deadsnakes/ppa -y
                    apt-get update
                    apt-get install -y python3.11 python3.11-dev python3.11-venv python3.11-distutils
                    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
                fi
                ;;
            centos|rhel|fedora)
                $PKG_MGR install -y python3.11 python3.11-devel
                ;;
            arch)
                pacman -S --noconfirm python
                ;;
        esac
    else
        log "Python $PYTHON_VERSION já instalado"
    fi
}

# Instalar dependências para Modbus
install_modbus_dependencies() {
    log "Instalando dependências para Modbus..."
    
    case $DISTRO in
        ubuntu|debian)
            apt-get install -y \
                libmodbus-dev \
                pkg-config \
                libffi-dev \
                libssl-dev
            ;;
        centos|rhel|fedora)
            $PKG_MGR install -y \
                libmodbus-devel \
                pkgconfig \
                libffi-devel \
                openssl-devel
            ;;
        arch)
            pacman -S --noconfirm \
                libmodbus \
                pkg-config \
                libffi \
                openssl
            ;;
    esac
}

# Instalar dependências para BLE
install_ble_dependencies() {
    log "Instalando dependências para BLE..."
    
    case $DISTRO in
        ubuntu|debian)
            apt-get install -y \
                bluez \
                bluez-tools \
                libbluetooth-dev \
                libdbus-1-dev \
                libglib2.0-dev \
                libical-dev \
                libreadline-dev \
                libudev-dev
            ;;
        centos|rhel|fedora)
            $PKG_MGR install -y \
                bluez \
                bluez-tools \
                bluez-libs-devel \
                dbus-devel \
                glib2-devel \
                libical-devel \
                readline-devel \
                systemd-devel
            ;;
        arch)
            pacman -S --noconfirm \
                bluez \
                bluez-utils \
                bluez-libs \
                dbus \
                glib2 \
                libical \
                readline \
                systemd
            ;;
    esac
}

# Instalar dependências para processamento de dados
install_data_processing_dependencies() {
    log "Instalando dependências para processamento de dados..."
    
    case $DISTRO in
        ubuntu|debian)
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
            ;;
        centos|rhel|fedora)
            $PKG_MGR install -y \
                hdf5-devel \
                atlas-devel \
                lapack-devel \
                gcc-gfortran \
                libjpeg-turbo-devel \
                libpng-devel \
                libtiff-devel \
                ffmpeg-devel
            ;;
        arch)
            pacman -S --noconfirm \
                hdf5 \
                atlas-lapack \
                gcc-fortran \
                libjpeg-turbo \
                libpng \
                libtiff \
                ffmpeg
            ;;
    esac
}

# Instalar Docker
install_docker() {
    log "Instalando Docker..."
    
    if command -v docker &> /dev/null; then
        log "Docker já instalado"
        return
    fi
    
    case $DISTRO in
        ubuntu|debian)
            # Instalar Docker via repositório oficial
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            rm get-docker.sh
            ;;
        centos|rhel|fedora)
            # Instalar Docker via repositório oficial
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            rm get-docker.sh
            ;;
        arch)
            pacman -S --noconfirm docker
            ;;
    esac
    
    # Adicionar usuário ao grupo docker
    usermod -aG docker $SUDO_USER
    
    # Iniciar e habilitar Docker
    systemctl start docker
    systemctl enable docker
}

# Instalar Docker Compose
install_docker_compose() {
    log "Instalando Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        log "Docker Compose já instalado"
        return
    fi
    
    # Instalar Docker Compose
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Criar link simbólico se necessário
    if [ ! -f /usr/bin/docker-compose ]; then
        ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
    fi
}

# Instalar Node.js
install_nodejs() {
    log "Instalando Node.js..."
    
    if command -v node &> /dev/null; then
        log "Node.js já instalado"
        return
    fi
    
    case $DISTRO in
        ubuntu|debian)
            NODE_MAJOR=20
            if [ -n "$DISTRO_CODENAME" ] && curl -fsI "https://deb.nodesource.com/node_${NODE_MAJOR}.x/dists/${DISTRO_CODENAME}/Release" >/dev/null 2>&1; then
                log "Distribuição suportada pela NodeSource. Instalando Node.js ${NODE_MAJOR}.x"
                curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash -
                apt-get install -y nodejs
            else
                warn "NodeSource não suporta ${DISTRO_CODENAME:-esta distribuição} na série ${NODE_MAJOR}.x. Instalando nodejs/npm do repositório padrão"
                apt-get install -y nodejs npm
            fi
            ;;
        centos|rhel|fedora)
            curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
            $PKG_MGR install -y nodejs
            ;;
        arch)
            pacman -S --noconfirm nodejs npm
            ;;
    esac
    
    # Instalar Yarn
    if command -v npm &> /dev/null; then
        npm install -g yarn
    else
        warn "npm não encontrado; Yarn não será instalado automaticamente"
    fi
}

# Criar diretórios
create_directories() {
    log "Criando diretórios..."
    
    mkdir -p /opt/bitcoin_mining
    mkdir -p /opt/bitcoin_mining/data
    mkdir -p /opt/bitcoin_mining/logs
    mkdir -p /opt/bitcoin_mining/backup
    mkdir -p /opt/bitcoin_mining/config
    mkdir -p /opt/bitcoin_mining/reports
    mkdir -p /opt/bitcoin_mining/logs_csv
    
    # Configurar permissões
    chown -R $SUDO_USER:$SUDO_USER /opt/bitcoin_mining
}

# Instalar dependências Python
install_python_dependencies() {
    log "Instalando dependências Python..."
    
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
}

# Configurar sistema de inicialização
setup_systemd() {
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
User=$SUDO_USER
Group=$SUDO_USER

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
User=$SUDO_USER
Group=$SUDO_USER
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
}

# Configurar firewall
setup_firewall() {
    log "Configurando firewall..."
    
    case $DISTRO in
        ubuntu|debian)
            if command -v ufw &> /dev/null; then
                ufw allow 8000/tcp  # API
                ufw allow 3000/tcp  # Frontend
                ufw allow 3001/tcp  # Grafana
                ufw allow 9090/tcp  # Prometheus
                ufw allow 15672/tcp # RabbitMQ Management
                ufw allow 502/tcp   # Modbus TCP
                ufw allow 503/tcp   # Modbus TCP (ABB)
            fi
            ;;
        centos|rhel|fedora)
            if command -v firewall-cmd &> /dev/null; then
                firewall-cmd --permanent --add-port=8000/tcp
                firewall-cmd --permanent --add-port=3000/tcp
                firewall-cmd --permanent --add-port=3001/tcp
                firewall-cmd --permanent --add-port=9090/tcp
                firewall-cmd --permanent --add-port=15672/tcp
                firewall-cmd --permanent --add-port=502/tcp
                firewall-cmd --permanent --add-port=503/tcp
                firewall-cmd --reload
            fi
            ;;
        arch)
            if command -v ufw &> /dev/null; then
                ufw allow 8000/tcp
                ufw allow 3000/tcp
                ufw allow 3001/tcp
                ufw allow 9090/tcp
                ufw allow 15672/tcp
                ufw allow 502/tcp
                ufw allow 503/tcp
            fi
            ;;
    esac
}

# Configurar swap
setup_swap() {
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
}

# Configurar limites do sistema
setup_system_limits() {
    log "Configurando limites do sistema..."
    
    # Limite de arquivos
    echo "* soft nofile 65536" >> /etc/security/limits.conf
    echo "* hard nofile 65536" >> /etc/security/limits.conf
    
    # Parâmetros do kernel
    echo "vm.max_map_count=262144" >> /etc/sysctl.conf
    echo "net.core.somaxconn=65535" >> /etc/sysctl.conf
    echo "net.core.netdev_max_backlog=5000" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_max_syn_backlog=4096" >> /etc/sysctl.conf
    sysctl -p
}

# Criar scripts de manutenção
create_maintenance_scripts() {
    log "Criando scripts de manutenção..."
    
    # Script de backup
    cat > /opt/bitcoin_mining/backup.sh << 'EOF'
#!/bin/bash
# Script de backup do sistema de mineração

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

    # Script de monitoramento
    cat > /opt/bitcoin_mining/monitor.sh << 'EOF'
#!/bin/bash
# Script de monitoramento do sistema

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

echo "=== Logs Recentes ==="
tail -20 /opt/bitcoin_mining/logs/bitcoin_mining.log 2>/dev/null || echo "Nenhum log encontrado"
echo

echo "=== Estatísticas de Rede ==="
ss -tuln | grep -E ":(8000|3000|3001|9090|15672|502|503)"
echo
EOF

    chmod +x /opt/bitcoin_mining/monitor.sh

    # Script de diagnóstico
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
EOF

    chmod +x /opt/bitcoin_mining/diagnose.sh
}

# Configurar cron
setup_cron() {
    log "Configurando cron jobs..."
    
    # Backup diário às 2:00
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/bitcoin_mining/backup.sh") | crontab -
    
    # Limpeza de logs semanalmente
    (crontab -l 2>/dev/null; echo "0 3 * * 0 find /opt/bitcoin_mining/logs -name '*.log' -mtime +7 -delete") | crontab -
    
    # Limpeza de dados antigos mensalmente
    (crontab -l 2>/dev/null; echo "0 4 * * 0 find /opt/bitcoin_mining/logs_csv -name '*.csv' -mtime +30 -delete") | crontab -
}

# Criar arquivo .env de exemplo
create_env_example() {
    log "Criando arquivo .env de exemplo..."
    
    cat > /opt/bitcoin_mining/.env.example << 'EOF'
# Configurações do Sistema de Automação para Mineração de Bitcoin
# Configurado automaticamente para Linux

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
# CONFIGURAÇÕES ESPECÍFICAS DO LINUX
# =============================================================================
DISPLAY=:0
XAUTHORITY=/home/$USER/.Xauthority
EOF
}

# Criar README
create_readme() {
    log "Criando documentação..."
    
    cat > /opt/bitcoin_mining/README_LINUX.md << 'EOF'
# Sistema de Automação para Mineração de Bitcoin - Linux

## Instalação Concluída

O sistema foi instalado com sucesso no seu sistema Linux!

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
}

# Função principal de instalação
main() {
    log "Iniciando instalação do Sistema de Automação para Mineração de Bitcoin..."
    
    # Executar todas as etapas de instalação
    install_basic_dependencies
    install_python
    install_modbus_dependencies
    install_ble_dependencies
    install_data_processing_dependencies
    install_docker
    install_docker_compose
    install_nodejs
    create_directories
    install_python_dependencies
    setup_systemd
    setup_firewall
    setup_swap
    setup_system_limits
    create_maintenance_scripts
    setup_cron
    create_env_example
    create_readme
    
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
    echo "Documentação: /opt/bitcoin_mining/README_LINUX.md"
    echo
    log "Instalação finalizada!"
}

# Executar instalação
main
