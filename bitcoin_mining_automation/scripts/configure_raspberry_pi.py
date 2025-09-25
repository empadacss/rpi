#!/usr/bin/env python3
"""
Script de configuração específico para Raspberry Pi
Sistema de Automação para Mineração de Bitcoin
"""

import os
import sys
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime

class RaspberryPiConfigurator:
    """Classe para configurar o sistema no Raspberry Pi"""
    
    def __init__(self):
        self.base_path = Path("/opt/bitcoin_mining")
        self.config_path = self.base_path / "config"
        self.data_path = self.base_path / "data"
        self.logs_path = self.base_path / "logs"
        self.reports_path = self.base_path / "reports"
        self.backup_path = self.base_path / "backup"
        
    def create_directories(self):
        """Criar diretórios necessários"""
        print("Criando diretórios...")
        
        directories = [
            self.config_path,
            self.data_path,
            self.logs_path,
            self.reports_path,
            self.backup_path,
            self.logs_path / "csv",
            self.data_path / "inverter",
            self.data_path / "multimedidor",
            self.data_path / "f2pool",
            self.data_path / "environmental",
            self.data_path / "asic",
            self.data_path / "reports"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ {directory}")
    
    def create_env_file(self):
        """Criar arquivo .env"""
        print("Criando arquivo .env...")
        
        env_content = """# Configurações do Sistema de Automação para Mineração de Bitcoin
# Configurado automaticamente para Raspberry Pi

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
"""
        
        env_file = self.base_path / ".env"
        with open(env_file, "w") as f:
            f.write(env_content)
        
        print(f"✅ {env_file}")
    
    def create_devices_config(self):
        """Criar configuração de dispositivos"""
        print("Criando configuração de dispositivos...")
        
        devices_config = {
            "inverter": {
                "host": "192.168.0.111",
                "port": 502,
                "slave_id": 1,
                "registers": {
                    "speed": {"address": 0x1000, "type": "uint16"},
                    "frequency": {"address": 0x1001, "type": "uint16"},
                    "current": {"address": 0x1002, "type": "uint16"},
                    "temperature": {"address": 0x1003, "type": "uint16"}
                }
            },
            "multimedidor": {
                "host": "192.168.0.108",
                "port": 503,
                "slave_id": 1,
                "registers": {
                    "voltage": {"address": 0x2000, "type": "uint16"},
                    "current": {"address": 0x2001, "type": "uint16"},
                    "power": {"address": 0x2002, "type": "uint16"},
                    "energy": {"address": 0x2003, "type": "uint32"}
                }
            },
            "ble_sensors": {
                "sensor_1": {
                    "mac": "A4:C1:38:30:26:23",
                    "name": "Sensor Sala 1",
                    "location": "Sala Principal"
                },
                "sensor_2": {
                    "mac": "A4:C1:38:65:D8:21",
                    "name": "Sensor Sala 2",
                    "location": "Sala Secundária"
                }
            },
            "asics": {
                "discovery": {
                    "enabled": True,
                    "network_range": "192.168.0.0/24",
                    "scan_interval": 300
                },
                "control": {
                    "enabled": True,
                    "hashcore_path": "/usr/local/bin/hashcore",
                    "timeout": 30,
                    "retry_attempts": 3
                }
            },
            "f2pool": {
                "api_token": "your_f2pool_api_token_here",
                "pool_url": "https://api.f2pool.com",
                "mining_user": "USER",
                "currency": "BTC",
                "update_interval": 60
            }
        }
        
        devices_file = self.config_path / "devices.yaml"
        with open(devices_file, "w") as f:
            yaml.dump(devices_config, f, default_flow_style=False, indent=2)
        
        print(f"✅ {devices_file}")
    
    def create_automation_config(self):
        """Criar configuração de automação"""
        print("Criando configuração de automação...")
        
        automation_config = {
            "safety_rules": {
                "inverter_not_run": {
                    "enabled": True,
                    "timeout": 30,
                    "action": "sleep_asics"
                },
                "humidity_critical": {
                    "enabled": True,
                    "threshold": 90.0,
                    "action": "adjust_fan_speed",
                    "fan_speed": 20
                },
                "dew_point_difference": {
                    "enabled": True,
                    "threshold": 4.0,
                    "action": "adjust_fan_speed",
                    "fan_speed": 10
                }
            },
            "schedules": {
                "asic_sleep": {
                    "enabled": True,
                    "time": "22:00",
                    "action": "sleep_all_asics"
                },
                "asic_resume": {
                    "enabled": True,
                    "time": "06:00",
                    "action": "resume_all_asics"
                },
                "fan_speed_adjust": {
                    "enabled": True,
                    "time": "12:00",
                    "action": "adjust_fan_speed",
                    "fan_speed": 15
                }
            },
            "alerts": {
                "connection_timeout": {
                    "enabled": True,
                    "timeout": 30,
                    "channels": ["whatsapp", "telegram", "email"]
                },
                "temperature_high": {
                    "enabled": True,
                    "threshold": 80.0,
                    "channels": ["whatsapp", "telegram", "email"]
                },
                "efficiency_low": {
                    "enabled": True,
                    "threshold": 0.8,
                    "channels": ["whatsapp", "telegram"]
                }
            }
        }
        
        automation_file = self.config_path / "automation.yaml"
        with open(automation_file, "w") as f:
            yaml.dump(automation_config, f, default_flow_style=False, indent=2)
        
        print(f"✅ {automation_file}")
    
    def create_logging_config(self):
        """Criar configuração de logging"""
        print("Criando configuração de logging...")
        
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": str(self.logs_path / "bitcoin_mining.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": str(self.logs_path / "errors.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": "DEBUG",
                    "propagate": False
                },
                "error": {
                    "handlers": ["error_file"],
                    "level": "ERROR",
                    "propagate": False
                }
            }
        }
        
        logging_file = self.config_path / "logging.yaml"
        with open(logging_file, "w") as f:
            yaml.dump(logging_config, f, default_flow_style=False, indent=2)
        
        print(f"✅ {logging_file}")
    
    def create_docker_compose(self):
        """Criar docker-compose.yml"""
        print("Criando docker-compose.yml...")
        
        docker_compose = """version: '3.8'

services:
  app:
    build: .
    container_name: bitcoin_mining_app
    restart: unless-stopped
    ports:
      - "8000:8000"
      - "3000:3000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
      - ./reports:/app/reports
    environment:
      - DATABASE_URL=postgresql://bitcoin_mining:password@postgres:5432/bitcoin_mining
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672
    depends_on:
      - postgres
      - redis
      - rabbitmq
    networks:
      - bitcoin_mining_network

  postgres:
    image: postgres:15
    container_name: bitcoin_mining_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: bitcoin_mining
      POSTGRES_USER: bitcoin_mining
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - bitcoin_mining_network

  redis:
    image: redis:7-alpine
    container_name: bitcoin_mining_redis
    restart: unless-stopped
    networks:
      - bitcoin_mining_network

  rabbitmq:
    image: rabbitmq:3-management
    container_name: bitcoin_mining_rabbitmq
    restart: unless-stopped
    ports:
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    networks:
      - bitcoin_mining_network

  grafana:
    image: grafana/grafana:latest
    container_name: bitcoin_mining_grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - bitcoin_mining_network

  prometheus:
    image: prom/prometheus:latest
    container_name: bitcoin_mining_prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - bitcoin_mining_network

  ollama:
    image: ollama/ollama:latest
    container_name: bitcoin_mining_ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - bitcoin_mining_network

volumes:
  postgres_data:
  grafana_data:
  prometheus_data:
  ollama_data:

networks:
  bitcoin_mining_network:
    driver: bridge
"""
        
        docker_file = self.base_path / "docker-compose.yml"
        with open(docker_file, "w") as f:
            f.write(docker_compose)
        
        print(f"✅ {docker_file}")
    
    def create_requirements(self):
        """Criar requirements.txt"""
        print("Criando requirements.txt...")
        
        requirements = """# Dependências principais
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1

# Dependências para Modbus
pymodbus==3.5.2

# Dependências para BLE
bleak==0.21.1
atc-mi-interface==0.0.1

# Dependências para ASICs
pyasic==0.0.1

# Dependências para processamento de dados
pandas==2.1.4
numpy==1.25.2
matplotlib==3.8.2
seaborn==0.13.0
plotly==5.17.0

# Dependências para interface gráfica
tkinter
ttkbootstrap==1.10.1
pillow==10.1.0

# Dependências para automação
schedule==1.2.0
tenacity==8.2.3

# Dependências para notificações
requests==2.31.0
httpx==0.25.2

# Dependências para monitoramento
prometheus-client==0.19.0
structlog==23.2.0
loguru==0.7.2

# Dependências para desenvolvimento
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
isort==5.12.0
flake8==6.1.0

# Dependências para processamento de dados
scikit-learn==1.3.2
scipy==1.11.4
opencv-python==4.8.1.78

# Dependências para LLM
ollama==0.1.7
openai==1.3.7

# Dependências para WebSocket
websockets==12.0
python-multipart==0.0.6

# Dependências para configuração
python-dotenv==1.0.0
pyyaml==6.0.1
"""
        
        requirements_file = self.base_path / "requirements.txt"
        with open(requirements_file, "w") as f:
            f.write(requirements)
        
        print(f"✅ {requirements_file}")
    
    def create_startup_script(self):
        """Criar script de inicialização"""
        print("Criando script de inicialização...")
        
        startup_script = """#!/bin/bash
# Script de inicialização do sistema de mineração

echo "Iniciando Sistema de Automação para Mineração de Bitcoin..."

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "Por favor, execute como root (sudo ./start.sh)"
    exit 1
fi

# Verificar se Docker está rodando
if ! systemctl is-active --quiet docker; then
    echo "Iniciando Docker..."
    systemctl start docker
fi

# Verificar se Docker Compose está disponível
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose não encontrado. Instalando..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Navegar para o diretório do projeto
cd /opt/bitcoin_mining

# Verificar se arquivo .env existe
if [ ! -f ".env" ]; then
    echo "Arquivo .env não encontrado. Copiando de .env.example..."
    cp .env.example .env
    echo "Por favor, configure o arquivo .env antes de continuar."
    exit 1
fi

# Verificar se configuração de dispositivos existe
if [ ! -f "config/devices.yaml" ]; then
    echo "Configuração de dispositivos não encontrada. Criando..."
    python3 scripts/configure_raspberry_pi.py
fi

# Iniciar serviços
echo "Iniciando serviços..."
docker-compose up -d

# Aguardar serviços iniciarem
echo "Aguardando serviços iniciarem..."
sleep 30

# Verificar status
echo "Verificando status dos serviços..."
docker-compose ps

# Verificar logs
echo "Verificando logs..."
docker-compose logs --tail=20

echo "Sistema iniciado com sucesso!"
echo "Acesse: http://$(hostname -I | awk '{print $1}'):8000"
echo "Grafana: http://$(hostname -I | awk '{print $1}'):3001"
echo "Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
"""
        
        startup_file = self.base_path / "start.sh"
        with open(startup_file, "w") as f:
            f.write(startup_script)
        
        # Tornar executável
        os.chmod(startup_file, 0o755)
        
        print(f"✅ {startup_file}")
    
    def create_stop_script(self):
        """Criar script de parada"""
        print("Criando script de parada...")
        
        stop_script = """#!/bin/bash
# Script de parada do sistema de mineração

echo "Parando Sistema de Automação para Mineração de Bitcoin..."

# Navegar para o diretório do projeto
cd /opt/bitcoin_mining

# Parar serviços
echo "Parando serviços..."
docker-compose down

# Parar serviço Python (se estiver rodando)
systemctl stop bitcoin-mining-python.service

echo "Sistema parado com sucesso!"
"""
        
        stop_file = self.base_path / "stop.sh"
        with open(stop_file, "w") as f:
            f.write(stop_script)
        
        # Tornar executável
        os.chmod(stop_file, 0o755)
        
        print(f"✅ {stop_file}")
    
    def create_restart_script(self):
        """Criar script de reinicialização"""
        print("Criando script de reinicialização...")
        
        restart_script = """#!/bin/bash
# Script de reinicialização do sistema de mineração

echo "Reiniciando Sistema de Automação para Mineração de Bitcoin..."

# Parar sistema
./stop.sh

# Aguardar
sleep 10

# Iniciar sistema
./start.sh
"""
        
        restart_file = self.base_path / "restart.sh"
        with open(restart_file, "w") as f:
            f.write(restart_script)
        
        # Tornar executável
        os.chmod(restart_file, 0o755)
        
        print(f"✅ {restart_file}")
    
    def create_status_script(self):
        """Criar script de status"""
        print("Criando script de status...")
        
        status_script = """#!/bin/bash
# Script de status do sistema de mineração

echo "=== Status do Sistema de Mineração ==="
echo "Data: $(date)"
echo

echo "=== Serviços Docker ==="
cd /opt/bitcoin_mining
docker-compose ps
echo

echo "=== Uso de Recursos ==="
echo "CPU:"
top -bn1 | grep "Cpu(s)"
echo

echo "Memória:"
free -h
echo

echo "Disco:"
df -h
echo

echo "=== Temperatura ==="
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    temp=$(cat /sys/class/thermal/thermal_zone0/temp)
    temp_c=$((temp/1000))
    echo "Temperatura da CPU: ${temp_c}°C"
fi
echo

echo "=== Logs Recentes ==="
tail -20 logs/bitcoin_mining.log 2>/dev/null || echo "Nenhum log encontrado"
echo

echo "=== Portas Abertas ==="
ss -tuln | grep -E ":(8000|3000|3001|9090|15672|502|503)"
echo

echo "=== Status dos Sensores BLE ==="
if command -v bluetoothctl &> /dev/null; then
    bluetoothctl show | grep "Powered"
    bluetoothctl devices | wc -l | xargs echo "Dispositivos BLE encontrados:"
fi
"""
        
        status_file = self.base_path / "status.sh"
        with open(status_file, "w") as f:
            f.write(status_script)
        
        # Tornar executável
        os.chmod(status_file, 0o755)
        
        print(f"✅ {status_file}")
    
    def create_cron_jobs(self):
        """Criar jobs do cron"""
        print("Criando jobs do cron...")
        
        # Backup diário às 2:00
        cron_backup = "0 2 * * * /opt/bitcoin_mining/backup.sh"
        
        # Limpeza de logs semanalmente
        cron_logs = "0 3 * * 0 find /opt/bitcoin_mining/logs -name '*.log' -mtime +7 -delete"
        
        # Limpeza de dados antigos mensalmente
        cron_data = "0 4 * * 0 find /opt/bitcoin_mining/logs_csv -name '*.csv' -mtime +30 -delete"
        
        # Adicionar jobs ao crontab
        import subprocess
        
        # Obter crontab atual
        try:
            current_crontab = subprocess.check_output(['crontab', '-l'], stderr=subprocess.DEVNULL).decode()
        except subprocess.CalledProcessError:
            current_crontab = ""
        
        # Adicionar novos jobs se não existirem
        new_jobs = []
        for job in [cron_backup, cron_logs, cron_data]:
            if job not in current_crontab:
                new_jobs.append(job)
        
        if new_jobs:
            # Adicionar jobs ao crontab
            all_jobs = current_crontab + "\n".join(new_jobs) + "\n"
            subprocess.run(['crontab', '-'], input=all_jobs, text=True)
            print("✅ Jobs do cron adicionados")
        else:
            print("✅ Jobs do cron já existem")
    
    def create_systemd_service(self):
        """Criar serviço systemd"""
        print("Criando serviço systemd...")
        
        service_content = f"""[Unit]
Description=Bitcoin Mining Automation System
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory={self.base_path}
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=root
Group=root

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/bitcoin-mining.service")
        with open(service_file, "w") as f:
            f.write(service_content)
        
        # Recarregar systemd
        subprocess.run(['systemctl', 'daemon-reload'])
        subprocess.run(['systemctl', 'enable', 'bitcoin-mining.service'])
        
        print(f"✅ {service_file}")
    
    def run_configuration(self):
        """Executar configuração completa"""
        print("Iniciando configuração do sistema...")
        
        try:
            # Criar diretórios
            self.create_directories()
            
            # Criar arquivos de configuração
            self.create_env_file()
            self.create_devices_config()
            self.create_automation_config()
            self.create_logging_config()
            
            # Criar Docker Compose
            self.create_docker_compose()
            
            # Criar requirements
            self.create_requirements()
            
            # Criar scripts
            self.create_startup_script()
            self.create_stop_script()
            self.create_restart_script()
            self.create_status_script()
            
            # Configurar cron
            self.create_cron_jobs()
            
            # Configurar systemd
            self.create_systemd_service()
            
            print("\n✅ Configuração concluída com sucesso!")
            print("\nPróximos passos:")
            print("1. Configure o arquivo .env com suas credenciais")
            print("2. Configure o arquivo config/devices.yaml com seus dispositivos")
            print("3. Execute: ./start.sh")
            print("4. Acesse: http://localhost:8000")
            
        except Exception as e:
            print(f"❌ Erro durante a configuração: {e}")
            return False
        
        return True

def main():
    """Função principal"""
    print("Configurador do Sistema de Automação para Mineração de Bitcoin")
    print("Raspberry Pi - Versão Aprimorada")
    print("=" * 50)
    
    # Verificar se está rodando como root
    if os.geteuid() != 0:
        print("❌ Este script deve ser executado como root (sudo)")
        sys.exit(1)
    
    # Verificar se está no diretório correto
    if not Path("/opt/bitcoin_mining").exists():
        print("❌ Diretório /opt/bitcoin_mining não encontrado")
        print("Execute primeiro o script de instalação")
        sys.exit(1)
    
    # Executar configuração
    configurator = RaspberryPiConfigurator()
    success = configurator.run_configuration()
    
    if success:
        print("\n🎉 Sistema configurado com sucesso!")
        print("Execute './start.sh' para iniciar o sistema")
    else:
        print("\n❌ Falha na configuração")
        sys.exit(1)

if __name__ == "__main__":
    main()


