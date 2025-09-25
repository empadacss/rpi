# Sistema de Automação para Mineração de Bitcoin

## 🚀 Instalação Rápida

### Para Linux (Ubuntu, Debian, CentOS, RHEL, Fedora, Arch)
```bash
# Baixar e executar instalação
wget https://raw.githubusercontent.com/seu-usuario/bitcoin-mining-automation/main/install_linux.sh
chmod +x install_linux.sh
sudo ./install_linux.sh
```

### Para Raspberry Pi com Ubuntu
```bash
# Baixar e executar instalação
wget https://raw.githubusercontent.com/seu-usuario/bitcoin-mining-automation/main/scripts/install_ubuntu_raspberry_pi.sh
chmod +x install_ubuntu_raspberry_pi.sh
sudo ./install_ubuntu_raspberry_pi.sh
```

### Para Raspberry Pi com Raspbian
```bash
# Baixar e executar instalação
wget https://raw.githubusercontent.com/seu-usuario/bitcoin-mining-automation/main/scripts/install_raspberry_pi_enhanced.sh
chmod +x install_raspberry_pi_enhanced.sh
sudo ./install_raspberry_pi_enhanced.sh
```

## ⚡ Inicialização Rápida

### Linux
```bash
cd /opt/bitcoin_mining
sudo ./quick_start_linux.sh
```

### Raspberry Pi
```bash
cd /opt/bitcoin_mining
sudo ./quick_start_ubuntu.sh
```

## 📋 Configuração

### 1. Configurar Variáveis de Ambiente
```bash
cd /opt/bitcoin_mining
cp .env.example .env
nano .env
```

### 2. Configurar Dispositivos
```bash
nano config/devices.yaml
```

### 3. Iniciar Sistema
```bash
# Opção A: Docker (Recomendado)
docker-compose up -d

# Opção B: Python direto
source .venv/bin/activate
python main.py

# Opção C: Serviço do sistema
sudo systemctl start bitcoin-mining-python.service
```

## 🔧 Comandos Úteis

### Monitoramento
```bash
./monitor.sh          # Status completo
./diagnose.sh         # Diagnóstico
tail -f logs/bitcoin_mining.log  # Logs em tempo real
```

### Manutenção
```bash
./backup.sh           # Backup manual
./update.sh           # Atualizar sistema
```

### Testes
```bash
python test_linux.py  # Testar sistema (Linux)
python scripts/test_raspberry_pi.py  # Testar sistema (Raspberry Pi)
```

## 🌐 Interfaces Disponíveis

- **API**: http://seu-ip:8000
- **Frontend**: http://seu-ip:3000
- **Grafana**: http://seu-ip:3001
- **Prometheus**: http://seu-ip:9090
- **RabbitMQ**: http://seu-ip:15672

## 📚 Documentação

### Guias Detalhados
- [Guia de Instalação Linux](GUIA_INSTALACAO_LINUX.md)
- [Guia de Execução Raspberry Pi Ubuntu](GUIA_EXECUCAO_RASPBERRY_PI_UBUNTU.md)

### Scripts de Instalação
- [install_linux.sh](install_linux.sh) - Instalação universal para Linux
- [scripts/install_ubuntu_raspberry_pi.sh](scripts/install_ubuntu_raspberry_pi.sh) - Raspberry Pi com Ubuntu
- [scripts/install_raspberry_pi_enhanced.sh](scripts/install_raspberry_pi_enhanced.sh) - Raspberry Pi com Raspbian

### Scripts de Inicialização
- [quick_start_linux.sh](quick_start_linux.sh) - Inicialização rápida Linux
- [scripts/quick_start_ubuntu.sh](scripts/quick_start_ubuntu.sh) - Inicialização rápida Raspberry Pi

### Scripts de Teste
- [test_linux.py](test_linux.py) - Testes para Linux
- [scripts/test_raspberry_pi.py](scripts/test_raspberry_pi.py) - Testes para Raspberry Pi

## 🎯 Funcionalidades

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

## 🔧 Configuração de Dispositivos

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

## 📊 Monitoramento

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

## 🚨 Solução de Problemas

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

## 🔄 Atualizações e Backup

### Backup Automático
- **Frequência**: Diário às 2:00
- **Retenção**: 7 backups
- **Localização**: `/opt/bitcoin_mining/backup/`

### Backup Manual
```bash
./backup.sh
```

### Atualização
```bash
./update.sh
```

## 📱 Acesso Remoto

### SSH
```bash
ssh usuario@IP_DO_SERVIDOR
```

### Interface Web
- **API**: http://IP_DO_SERVIDOR:8000
- **Frontend**: http://IP_DO_SERVIDOR:3000
- **Grafana**: http://IP_DO_SERVIDOR:3001

## 🔒 Segurança

### Configurações de Segurança
```bash
# Configurar firewall
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 8000
sudo ufw allow 3000

# Configurar SSH
sudo nano /etc/ssh/sshd_config
```

### Backup de Segurança
```bash
# Backup de configurações
tar -czf config_backup.tar.gz config/

# Backup de chaves
tar -czf keys_backup.tar.gz .env
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

---

**Sistema pronto para uso!** 🎉

Para suporte adicional, consulte a documentação específica para sua plataforma ou os logs em `/opt/bitcoin_mining/logs/`.