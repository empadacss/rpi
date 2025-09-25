#!/bin/bash

# Script de instalação para Raspberry Pi
# Sistema de Automação para Mineração de Bitcoin

set -e

echo "🚀 Instalando Sistema de Automação para Mineração de Bitcoin no Raspberry Pi"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    error "Por favor, execute como root (sudo ./install_raspberry_pi.sh)"
fi

# Verificar arquitetura
ARCH=$(uname -m)
if [[ "$ARCH" != "armv7l" && "$ARCH" != "aarch64" ]]; then
    warn "Arquitetura não detectada como ARM. Continuando mesmo assim..."
fi

log "Arquitetura detectada: $ARCH"

# Atualizar sistema
log "Atualizando sistema..."
apt-get update
apt-get upgrade -y

# Instalar dependências básicas
log "Instalando dependências básicas..."
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
    lsb-release

# Instalar Python 3.11
log "Instalando Python 3.11..."
apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip

# Instalar dependências para Modbus
log "Instalando dependências para Modbus..."
apt-get install -y \
    libmodbus-dev \
    pkg-config

# Instalar Docker
log "Instalando Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Adicionar usuário ao grupo docker
usermod -aG docker $SUDO_USER

# Instalar Docker Compose
log "Instalando Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verificar instalação do Docker
log "Verificando instalação do Docker..."
docker --version
docker-compose --version

# Criar diretórios
log "Criando diretórios..."
mkdir -p /opt/bitcoin_mining
mkdir -p /opt/bitcoin_mining/data
mkdir -p /opt/bitcoin_mining/logs
mkdir -p /opt/bitcoin_mining/backup
mkdir -p /opt/bitcoin_mining/config

# Configurar permissões
chown -R $SUDO_USER:$SUDO_USER /opt/bitcoin_mining

# Instalar HashCore Toolkit (se disponível)
log "Verificando HashCore Toolkit..."
if command -v hashcore &> /dev/null; then
    log "HashCore Toolkit já instalado"
else
    warn "HashCore Toolkit não encontrado. Instale manualmente se necessário."
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
User=$SUDO_USER
Group=$SUDO_USER

[Install]
WantedBy=multi-user.target
EOF

# Recarregar systemd
systemctl daemon-reload

# Habilitar serviço
systemctl enable bitcoin-mining.service

# Configurar firewall (se ufw estiver instalado)
if command -v ufw &> /dev/null; then
    log "Configurando firewall..."
    ufw allow 8000/tcp  # API
    ufw allow 3000/tcp  # Frontend
    ufw allow 3001/tcp  # Grafana
    ufw allow 9090/tcp  # Prometheus
    ufw allow 15672/tcp # RabbitMQ Management
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
sysctl -p

# Criar script de backup
log "Criando script de backup..."
cat > /opt/bitcoin_mining/backup.sh << 'EOF'
#!/bin/bash
# Script de backup do sistema de mineração

BACKUP_DIR="/opt/bitcoin_mining/backup"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="bitcoin_mining_backup_$DATE.tar.gz"

echo "Criando backup: $BACKUP_FILE"

# Parar serviços
docker-compose down

# Criar backup
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='backup' \
    --exclude='logs' \
    --exclude='data' \
    .

# Reiniciar serviços
docker-compose up -d

echo "Backup criado: $BACKUP_DIR/$BACKUP_FILE"
EOF

chmod +x /opt/bitcoin_mining/backup.sh

# Criar script de monitoramento
log "Criando script de monitoramento..."
cat > /opt/bitcoin_mining/monitor.sh << 'EOF'
#!/bin/bash
# Script de monitoramento do sistema

echo "=== Status do Sistema de Mineração ==="
echo "Data: $(date)"
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
docker-compose logs --tail=10
EOF

chmod +x /opt/bitcoin_mining/monitor.sh

# Criar script de atualização
log "Criando script de atualização..."
cat > /opt/bitcoin_mining/update.sh << 'EOF'
#!/bin/bash
# Script de atualização do sistema

echo "Atualizando sistema de mineração..."

# Fazer backup
./backup.sh

# Parar serviços
docker-compose down

# Atualizar código (se for um repositório git)
if [ -d ".git" ]; then
    git pull
fi

# Reconstruir e reiniciar
docker-compose up -d --build

echo "Sistema atualizado com sucesso!"
EOF

chmod +x /opt/bitcoin_mining/update.sh

# Configurar cron para backup automático
log "Configurando backup automático..."
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/bitcoin_mining/backup.sh") | crontab -

# Configurar cron para limpeza de logs
(crontab -l 2>/dev/null; echo "0 3 * * 0 find /opt/bitcoin_mining/logs -name '*.log' -mtime +7 -delete") | crontab -

# Criar arquivo .env de exemplo
log "Criando arquivo .env de exemplo..."
cat > /opt/bitcoin_mining/.env.example << 'EOF'
# Configurações do Sistema
DEBUG=false
LOG_LEVEL=INFO

# Banco de Dados
DATABASE_URL=postgresql://bitcoin_mining:password@postgres:5432/bitcoin_mining

# Redis
REDIS_URL=redis://redis:6379

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672

# LLM
LLM_MODE=local
LLM_ENDPOINT=http://ollama:11434

# Dispositivos
ABB_HOST=192.168.0.10
ABB_PORT=502
BLE_INTERFACE=/dev/ttyUSB0

# Pools
F2POOL_API_TOKEN=your_token_here
POOL_URL=https://api.f2pool.com

# Notificações
WHATSAPP_TOKEN=your_whatsapp_token
TELEGRAM_BOT_TOKEN=your_telegram_token
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASS=your_password

# Thresholds
TEMP_MAX=80.0
TEMP_CRITICAL=85.0
HUMIDITY_MAX=80.0
EFFICIENCY_MIN=0.8
EOF

# Criar README para o usuário
log "Criando documentação..."
cat > /opt/bitcoin_mining/README_RASPBERRY_PI.md << 'EOF'
# Sistema de Automação para Mineração de Bitcoin - Raspberry Pi

## Instalação Concluída

O sistema foi instalado com sucesso no seu Raspberry Pi!

## Próximos Passos

1. **Configurar variáveis de ambiente:**
   ```bash
   cp .env.example .env
   nano .env
   ```

2. **Iniciar o sistema:**
   ```bash
   docker-compose up -d
   ```

3. **Verificar status:**
   ```bash
   ./monitor.sh
   ```

4. **Acessar interfaces:**
   - API: http://seu-ip:8000
   - Frontend: http://seu-ip:3000
   - Grafana: http://seu-ip:3001
   - Prometheus: http://seu-ip:9090

## Comandos Úteis

- **Iniciar sistema:** `sudo systemctl start bitcoin-mining`
- **Parar sistema:** `sudo systemctl stop bitcoin-mining`
- **Ver logs:** `docker-compose logs -f`
- **Fazer backup:** `./backup.sh`
- **Atualizar:** `./update.sh`

## Monitoramento

O sistema inclui monitoramento completo com:
- Prometheus para métricas
- Grafana para visualização
- Alertas automáticos
- Logs centralizados

## Suporte

Para suporte, consulte a documentação completa ou abra uma issue no repositório.
EOF

# Finalizar instalação
log "Instalação concluída com sucesso!"
echo
echo "=========================================="
echo "🎉 Sistema instalado com sucesso!"
echo "=========================================="
echo
echo "Próximos passos:"
echo "1. cd /opt/bitcoin_mining"
echo "2. cp .env.example .env"
echo "3. nano .env  # Configure suas variáveis"
echo "4. docker-compose up -d"
echo "5. ./monitor.sh  # Verificar status"
echo
echo "Acesse: http://$(hostname -I | awk '{print $1}'):8000"
echo
echo "Documentação: /opt/bitcoin_mining/README_RASPBERRY_PI.md"
echo
log "Instalação finalizada!"


