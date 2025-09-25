#!/bin/bash

# Script para corrigir erro do PPA deadsnakes no Ubuntu 25.04
# Sistema de Automação para Mineração de Bitcoin

set -e

echo "🔧 Corrigindo erro do PPA deadsnakes no Ubuntu 25.04"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    error "Execute como root: sudo ./fix_ubuntu_25_ppa.sh"
fi

# Verificar versão do Ubuntu
UBUNTU_VERSION=$(lsb_release -rs)
log "Versão do Ubuntu detectada: $UBUNTU_VERSION"

if [[ "$UBUNTU_VERSION" == "25.04" ]]; then
    log "Ubuntu 25.04 detectado - corrigindo PPA..."
    
    # Remover PPA problemático
    log "Removendo PPA deadsnakes..."
    add-apt-repository --remove ppa:deadsnakes/ppa -y 2>/dev/null || true
    
    # Limpar cache do apt
    log "Limpando cache do apt..."
    apt-get clean
    apt-get autoclean
    
    # Atualizar lista de pacotes
    log "Atualizando lista de pacotes..."
    apt-get update
    
    # Verificar Python disponível
    log "Verificando Python disponível..."
    python3 --version
    
    # Instalar Python 3.12 (padrão do Ubuntu 25.04)
    log "Instalando Python 3.12..."
    apt-get install -y python3.12 python3.12-dev python3.12-venv python3.12-distutils
    
    # Configurar alternativas
    log "Configurando alternativas do Python..."
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
    
    # Verificar instalação
    log "Verificando instalação do Python..."
    python3 --version
    
    log "✅ Correção concluída com sucesso!"
    log "Python 3.12 instalado e configurado"
    
elif [[ "$UBUNTU_VERSION" == "24.04" ]]; then
    log "Ubuntu 24.04 detectado - aplicando correção similar..."
    
    # Remover PPA problemático
    log "Removendo PPA deadsnakes..."
    add-apt-repository --remove ppa:deadsnakes/ppa -y 2>/dev/null || true
    
    # Limpar cache do apt
    log "Limpando cache do apt..."
    apt-get clean
    apt-get autoclean
    
    # Atualizar lista de pacotes
    log "Atualizando lista de pacotes..."
    apt-get update
    
    # Instalar Python 3.12
    log "Instalando Python 3.12..."
    apt-get install -y python3.12 python3.12-dev python3.12-venv python3.12-distutils
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
    
    log "✅ Correção concluída com sucesso!"
    
else
    log "Ubuntu $UBUNTU_VERSION detectado - PPA deve funcionar normalmente"
    log "Se houver problemas, execute:"
    log "sudo add-apt-repository --remove ppa:deadsnakes/ppa -y"
    log "sudo apt-get update"
fi

echo
echo "=========================================="
echo "🎉 Correção do PPA concluída!"
echo "=========================================="
echo
echo "Agora você pode continuar com a instalação:"
echo "sudo ./install_ubuntu_raspberry_pi.sh"
echo
