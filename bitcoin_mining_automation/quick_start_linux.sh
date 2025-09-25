#!/bin/bash

# Script de inicialização rápida para Linux
# Sistema de Automação para Mineração de Bitcoin

set -e

echo "🚀 Inicialização Rápida - Sistema de Mineração Bitcoin"
echo "Linux Universal"
echo "=========================================="

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] INFO: $1${NC}"
}

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    error "Execute como root: sudo ./quick_start_linux.sh"
fi

# Verificar se o sistema já está instalado
if [ ! -d "/opt/bitcoin_mining" ]; then
    error "Sistema não instalado. Execute primeiro: sudo ./install_linux.sh"
fi

log "Iniciando sistema de mineração..."

# Navegar para o diretório
cd /opt/bitcoin_mining

# Verificar se arquivo .env existe
if [ ! -f ".env" ]; then
    warn "Arquivo .env não encontrado. Criando a partir do exemplo..."
    cp .env.example .env
    info "Configure o arquivo .env com suas credenciais: nano .env"
fi

# Verificar se configuração de dispositivos existe
if [ ! -f "config/devices.yaml" ]; then
    warn "Configuração de dispositivos não encontrada. Criando..."
    mkdir -p config
    cat > config/devices.yaml << 'EOF'
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
EOF
    info "Configure os dispositivos: nano config/devices.yaml"
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    error "Docker não encontrado. Execute o script de instalação completo."
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose não encontrado. Execute o script de instalação completo."
fi

# Verificar se Docker está rodando
if ! systemctl is-active --quiet docker; then
    log "Iniciando Docker..."
    systemctl start docker
fi

# Parar serviços existentes
log "Parando serviços existentes..."
systemctl stop bitcoin-mining-python.service 2>/dev/null || true
docker-compose down 2>/dev/null || true

# Iniciar serviços
log "Iniciando serviços..."

# Iniciar Docker Compose
log "Iniciando Docker Compose..."
docker-compose up -d

# Aguardar serviços iniciarem
log "Aguardando serviços iniciarem..."
sleep 30

# Verificar status dos containers
log "Verificando status dos containers..."
docker-compose ps

# Iniciar serviço Python (opcional)
log "Iniciando serviço Python..."
systemctl start bitcoin-mining-python.service

# Aguardar um pouco mais
sleep 10

# Verificar status final
log "Verificando status final..."

# Verificar se as portas estão abertas
PORTS=(8000 3000 3001 9090 15672)
for port in "${PORTS[@]}"; do
    if ss -tuln | grep -q ":$port "; then
        log "✅ Porta $port: ABERTA"
    else
        warn "⚠️ Porta $port: FECHADA"
    fi
done

# Verificar logs
log "Verificando logs..."
if [ -f "logs/bitcoin_mining.log" ]; then
    log "✅ Logs disponíveis"
    info "Últimas linhas do log:"
    tail -5 logs/bitcoin_mining.log
else
    warn "⚠️ Logs não encontrados"
fi

# Obter IP da máquina
IP=$(hostname -I | awk '{print $1}')

echo
echo "=========================================="
echo "🎉 Sistema iniciado com sucesso!"
echo "=========================================="
echo
echo "Interfaces disponíveis:"
echo "  API:        http://$IP:8000"
echo "  Frontend:   http://$IP:3000"
echo "  Grafana:    http://$IP:3001"
echo "  Prometheus: http://$IP:9090"
echo "  RabbitMQ:   http://$IP:15672"
echo
echo "Comandos úteis:"
echo "  Status:     ./monitor.sh"
echo "  Diagnóstico: ./diagnose.sh"
echo "  Logs:       tail -f logs/bitcoin_mining.log"
echo "  Parar:      docker-compose down"
echo "  Reiniciar:  ./restart.sh"
echo
echo "Configuração:"
echo "  Editar .env: nano .env"
echo "  Dispositivos: nano config/devices.yaml"
echo
echo "Documentação: README_LINUX.md"
echo "=========================================="

# Verificar se há alertas
if [ -f "logs/errors.log" ] && [ -s "logs/errors.log" ]; then
    warn "⚠️ Há erros nos logs. Verifique: tail -f logs/errors.log"
fi

log "Inicialização concluída!"
