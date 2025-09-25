# Guia para Salvar no GitHub

## 🚀 **Método 1: Script Automático (Recomendado)**

### **1. Preparar o Sistema**
```bash
# Navegar para a pasta do projeto
cd ~/Documents/bitcoin_mining_automation

# Tornar o script executável
chmod +x scripts/upload_to_github.sh

# Executar o script
./scripts/upload_to_github.sh
```

### **2. Seguir as Instruções**
O script vai pedir:
- Seu nome de usuário do GitHub
- Nome do repositório
- Descrição do projeto
- Seu nome completo
- Seu email

## 🔧 **Método 2: Manual (Passo a Passo)**

### **1. Instalar Git (se não estiver instalado)**
```bash
sudo apt update
sudo apt install git -y
```

### **2. Configurar Git**
```bash
# Configurar seu nome
git config --global user.name "Seu Nome"

# Configurar seu email
git config --global user.email "seu.email@gmail.com"

# Verificar configuração
git config --list
```

### **3. Inicializar Repositório**
```bash
# Navegar para a pasta do projeto
cd ~/Documents/bitcoin_mining_automation

# Inicializar Git
git init

# Adicionar arquivos
git add .

# Fazer commit inicial
git commit -m "Initial commit: Bitcoin Mining Automation System"
```

### **4. Criar Repositório no GitHub**
1. Acesse: https://github.com/new
2. Nome do repositório: `bitcoin-mining-automation`
3. Descrição: `Sistema de Automação para Mineração de Bitcoin`
4. Marque como **Público**
5. **NÃO** marque "Add a README file"
6. **NÃO** marque "Add .gitignore"
7. **NÃO** marque "Choose a license"
8. Clique em **"Create repository"**

### **5. Conectar com GitHub**
```bash
# Adicionar remote (substitua SEU_USUARIO pelo seu nome de usuário)
git remote add origin https://github.com/SEU_USUARIO/bitcoin-mining-automation.git

# Renomear branch para main
git branch -M main

# Fazer push
git push -u origin main
```

## 🔑 **Método 3: Com Token de Acesso**

### **1. Criar Token de Acesso**
1. Acesse: https://github.com/settings/tokens
2. Clique em **"Generate new token"**
3. Selecione **"repo"** (acesso completo aos repositórios)
4. Copie o token gerado

### **2. Usar Token para Push**
```bash
# Fazer push com token
git push https://SEU_TOKEN@github.com/SEU_USUARIO/bitcoin-mining-automation.git main
```

## 📁 **Estrutura do Projeto no GitHub**

```
bitcoin-mining-automation/
├── README.md                           # Documentação principal
├── GUIA_INSTALACAO_LINUX.md           # Guia de instalação
├── GUIA_EXECUCAO_RASPBERRY_PI_UBUNTU.md # Guia Raspberry Pi
├── GUIA_GITHUB.md                     # Este guia
├── install_linux.sh                   # Instalação Linux
├── quick_start_linux.sh               # Inicialização rápida
├── test_linux.py                      # Testes Linux
├── backend/                           # Código principal
│   ├── core/                         # Módulos principais
│   ├── api/                          # API REST
│   └── ...
├── scripts/                          # Scripts de instalação
│   ├── install_ubuntu_raspberry_pi.sh
│   ├── fix_ubuntu_25_ppa.sh
│   ├── upload_to_github.sh
│   └── ...
├── config/                           # Configurações
├── docs/                             # Documentação
└── .gitignore                        # Arquivos ignorados
```

## 🔄 **Atualizações Futuras**

### **Fazer Upload de Mudanças**
```bash
# Adicionar mudanças
git add .

# Fazer commit
git commit -m "Descrição das mudanças"

# Fazer push
git push origin main
```

### **Baixar Mudanças**
```bash
# Baixar mudanças do GitHub
git pull origin main
```

## 🛠️ **Comandos Úteis do Git**

### **Verificar Status**
```bash
# Ver status do repositório
git status

# Ver histórico de commits
git log --oneline

# Ver branches
git branch
```

### **Desfazer Mudanças**
```bash
# Desfazer mudanças não commitadas
git checkout -- arquivo.txt

# Desfazer último commit (mantendo mudanças)
git reset --soft HEAD~1

# Desfazer último commit (removendo mudanças)
git reset --hard HEAD~1
```

### **Criar Branch**
```bash
# Criar nova branch
git checkout -b nova-funcionalidade

# Trocar de branch
git checkout main

# Fazer merge
git merge nova-funcionalidade
```

## 🔒 **Configurações de Segurança**

### **Arquivo .gitignore**
O projeto já inclui um `.gitignore` que ignora:
- Arquivos de configuração sensíveis (`.env`)
- Logs e dados temporários
- Arquivos de backup
- Dependências Python (`.venv/`)
- Arquivos do sistema operacional

### **Variáveis de Ambiente**
Nunca commite arquivos `.env` com:
- Senhas
- Tokens de API
- Chaves privadas
- Configurações sensíveis

## 📋 **Checklist de Upload**

- [ ] Git configurado com nome e email
- [ ] Repositório inicializado (`git init`)
- [ ] Arquivos adicionados (`git add .`)
- [ ] Commit inicial feito (`git commit`)
- [ ] Repositório criado no GitHub
- [ ] Remote adicionado (`git remote add origin`)
- [ ] Push realizado (`git push -u origin main`)
- [ ] Repositório acessível no GitHub

## 🆘 **Solução de Problemas**

### **Erro: "Permission denied"**
```bash
# Configurar SSH (recomendado)
ssh-keygen -t rsa -b 4096 -C "seu.email@gmail.com"
cat ~/.ssh/id_rsa.pub
# Copiar a chave e adicionar no GitHub: Settings > SSH Keys
```

### **Erro: "Repository not found"**
```bash
# Verificar URL do remote
git remote -v

# Corrigir URL se necessário
git remote set-url origin https://github.com/SEU_USUARIO/REPOSITORIO.git
```

### **Erro: "Authentication failed"**
```bash
# Usar token de acesso
git push https://SEU_TOKEN@github.com/SEU_USUARIO/REPOSITORIO.git main
```

## 🎯 **Comandos Rápidos**

```bash
# Upload completo
cd ~/Documents/bitcoin_mining_automation
chmod +x scripts/upload_to_github.sh
./scripts/upload_to_github.sh

# Upload manual
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/SEU_USUARIO/bitcoin-mining-automation.git
git push -u origin main
```

---

**Projeto salvo no GitHub!** 🎉

Agora você pode:
- Compartilhar o projeto
- Colaborar com outros desenvolvedores
- Fazer backup do código
- Usar GitHub Actions para CI/CD
- Gerenciar versões e releases
