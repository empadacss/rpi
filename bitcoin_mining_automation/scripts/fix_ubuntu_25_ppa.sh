#!/bin/bash

# Script para corrigir erro do PPA deadsnakes no Ubuntu 25.x
# Sistema de Automação para Mineração de Bitcoin

set -e

echo "🔧 Corrigindo erro do PPA deadsnakes no Ubuntu 25.x"

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

case "$UBUNTU_VERSION" in
    25.*)
        log "Ubuntu $UBUNTU_VERSION detectado - corrigindo PPA..."

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
        python3 --version || true

        # Instalar Python 3.12 (padrão do Ubuntu 25)
        PYTHON_FIXED=false
        for candidate in 3.13 3.12; do
            if apt-cache show "python${candidate}" &> /dev/null; then
                log "Instalando Python ${candidate} e dependências..."
                apt-get install -y "python${candidate}" "python${candidate}-dev" "python${candidate}-venv"
                if apt-cache show "python${candidate}-distutils" &> /dev/null; then
                    apt-get install -y "python${candidate}-distutils"
                fi
                update-alternatives --install /usr/bin/python3 python3 "/usr/bin/python${candidate}" 1
                PYTHON_FIXED=true
                break
            fi
        done
        if [ "$PYTHON_FIXED" = false ]; then
            warn "Pacotes python3.12+ não encontrados. Garantindo pacotes genéricos python3."
            apt-get install -y python3 python3-dev python3-venv python3-pip
        else
            log "Python atualizado com sucesso"
        fi

        # Verificar instalação
        log "Verificando instalação do Python..."
        python3 --version

        log "✅ Correção concluída com sucesso!"
        log "Python $(python3 --version 2>/dev/null | awk '{print $2}') instalado e configurado"
        ;;
    24.*)
        log "Ubuntu $UBUNTU_VERSION detectado - aplicando correção semelhante..."

        log "Removendo PPA deadsnakes..."
        add-apt-repository --remove ppa:deadsnakes/ppa -y 2>/dev/null || true

        log "Limpando cache do apt..."
        apt-get clean
        apt-get autoclean

        log "Atualizando lista de pacotes..."
        apt-get update

        PYTHON_FIXED=false
        for candidate in 3.13 3.12; do
            if apt-cache show "python${candidate}" &> /dev/null; then
                log "Instalando Python ${candidate}..."
                apt-get install -y "python${candidate}" "python${candidate}-dev" "python${candidate}-venv"
                if apt-cache show "python${candidate}-distutils" &> /dev/null; then
                    apt-get install -y "python${candidate}-distutils"
                fi
                update-alternatives --install /usr/bin/python3 python3 "/usr/bin/python${candidate}" 1
                PYTHON_FIXED=true
                break
            fi
        done
        if [ "$PYTHON_FIXED" = false ]; then
            warn "Pacote python3.12+ não disponível. Usando pacotes genéricos python3"
            apt-get install -y python3 python3-dev python3-venv python3-pip
        else
            log "Python atualizado com sucesso"
        fi

        log "✅ Correção concluída com sucesso!"
        ;;
    *)
        log "Ubuntu $UBUNTU_VERSION detectado - PPA deve funcionar normalmente"
        log "Se houver problemas, execute:"
        log "sudo add-apt-repository --remove ppa:deadsnakes/ppa -y"
        log "sudo apt-get update"
        ;;
esac

echo
echo "=========================================="
echo "🎉 Correção do PPA concluída!"
echo "=========================================="
echo
echo "Agora você pode continuar com a instalação:"
echo "sudo ./install_ubuntu_raspberry_pi.sh"
echo
