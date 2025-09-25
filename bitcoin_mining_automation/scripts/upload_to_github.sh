#!/bin/bash

# Script para fazer upload do projeto para GitHub
# Sistema de Automação para Mineração de Bitcoin

set -e

echo "🚀 Fazendo upload do projeto para GitHub"

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

# Verificar se git está instalado
if ! command -v git &> /dev/null; then
    error "Git não está instalado. Instale com: sudo apt install git"
fi

# Verificar se estamos na pasta correta
if [ ! -f "README.md" ]; then
    error "Execute este script na pasta raiz do projeto (onde está o README.md)"
fi

# Solicitar informações do GitHub
echo "=========================================="
echo "CONFIGURAÇÃO DO GITHUB"
echo "=========================================="
echo

read -p "Digite seu nome de usuário do GitHub: " GITHUB_USERNAME
read -p "Digite o nome do repositório (ex: bitcoin-mining-automation): " REPO_NAME
read -p "Digite sua descrição do projeto: " REPO_DESCRIPTION

# Configurar Git
log "Configurando Git..."

# Verificar se git já está configurado
if ! git config --global user.name &> /dev/null; then
    read -p "Digite seu nome completo: " USER_NAME
    git config --global user.name "$USER_NAME"
fi

if ! git config --global user.email &> /dev/null; then
    read -p "Digite seu email: " USER_EMAIL
    git config --global user.email "$USER_EMAIL"
fi

# Inicializar repositório Git
log "Inicializando repositório Git..."
git init

# Criar .gitignore
log "Criando .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
logs/
*.log

# Data
data/
backup/
reports/
logs_csv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
.docker/

# Temporary files
*.tmp
*.temp
EOF

# Adicionar arquivos
log "Adicionando arquivos ao Git..."
git add .

# Fazer commit inicial
log "Fazendo commit inicial..."
git commit -m "Initial commit: Bitcoin Mining Automation System

- Sistema completo de automação para mineração de Bitcoin
- Suporte para Raspberry Pi com Ubuntu
- Monitoramento em tempo real (Modbus, BLE, F2Pool)
- Controle de ASICs via HashCore Toolkit
- Automação de segurança inteligente
- Interface gráfica moderna
- Sistema de logs e relatórios
- Documentação completa"

# Criar repositório no GitHub (via API)
log "Criando repositório no GitHub..."

# Verificar se gh CLI está instalado
if command -v gh &> /dev/null; then
    log "Usando GitHub CLI..."
    gh repo create "$REPO_NAME" --public --description "$REPO_DESCRIPTION" --source=. --remote=origin --push
else
    warn "GitHub CLI não encontrado. Criando repositório manualmente..."
    
    # Instruções para criar repositório manualmente
    echo
    echo "=========================================="
    echo "CRIAR REPOSITÓRIO NO GITHUB"
    echo "=========================================="
    echo
    echo "1. Acesse: https://github.com/new"
    echo "2. Nome do repositório: $REPO_NAME"
    echo "3. Descrição: $REPO_DESCRIPTION"
    echo "4. Marque como Público"
    echo "5. NÃO marque 'Add a README file'"
    echo "6. NÃO marque 'Add .gitignore'"
    echo "7. NÃO marque 'Choose a license'"
    echo "8. Clique em 'Create repository'"
    echo
    read -p "Pressione Enter após criar o repositório..."
    
    # Adicionar remote
    git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    
    # Fazer push
    log "Fazendo push para GitHub..."
    git branch -M main
    git push -u origin main
fi

# Verificar se o push foi bem-sucedido
if [ $? -eq 0 ]; then
    log "✅ Upload concluído com sucesso!"
    echo
    echo "=========================================="
    echo "🎉 PROJETO SALVO NO GITHUB!"
    echo "=========================================="
    echo
    echo "Repositório: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo
    echo "Próximos passos:"
    echo "1. Acesse o repositório no GitHub"
    echo "2. Configure as configurações do repositório"
    echo "3. Adicione colaboradores se necessário"
    echo "4. Configure GitHub Actions se desejar"
    echo
else
    error "Falha no upload para GitHub"
fi
