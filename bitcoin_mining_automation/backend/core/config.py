"""
Configuração central do sistema
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field
import yaml

class Config(BaseSettings):
    """Configuração central do sistema"""
    
    # Configurações da aplicação
    app_name: str = "Bitcoin Mining Automation"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Configurações do banco de dados
    database_url: str = Field(default="postgresql://user:password@localhost/bitcoin_mining", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Configurações da message queue
    rabbitmq_url: str = Field(default="amqp://localhost:5672", env="RABBITMQ_URL")
    
    # Configurações de LLM
    llm_mode: str = Field(default="disabled", env="LLM_MODE")  # disabled, local ou remote
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    llm_endpoint: Optional[str] = Field(default="http://localhost:11434", env="LLM_ENDPOINT")
    
    # Configurações de dispositivos
    abb_host: str = Field(default="192.168.0.10", env="ABB_HOST")
    abb_port: int = Field(default=502, env="ABB_PORT")
    ble_interface: str = Field(default="/dev/ttyUSB0", env="BLE_INTERFACE")
    
    # Configurações de pools
    f2pool_api_token: Optional[str] = Field(default=None, env="F2POOL_API_TOKEN")
    pool_url: str = Field(default="https://api.f2pool.com", env="POOL_URL")
    
    # Configurações de notificações
    whatsapp_token: Optional[str] = Field(default=None, env="WHATSAPP_TOKEN")
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_pass: Optional[str] = Field(default=None, env="SMTP_PASS")
    
    # Configurações de monitoramento
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    grafana_port: int = Field(default=3001, env="GRAFANA_PORT")
    
    # Configurações de coleta de dados
    collection_interval: int = Field(default=1, env="COLLECTION_INTERVAL")  # segundos
    queue_size: int = Field(default=1000, env="QUEUE_SIZE")
    
    # Configurações de alertas
    alert_cooldown: int = Field(default=300, env="ALERT_COOLDOWN")  # segundos
    max_alerts_per_hour: int = Field(default=10, env="MAX_ALERTS_PER_HOUR")
    
    # Configurações de ASICs
    asic_timeout: int = Field(default=30, env="ASIC_TIMEOUT")
    asic_retry_attempts: int = Field(default=3, env="ASIC_RETRY_ATTEMPTS")
    hashcore_path: str = Field(default="/usr/local/bin/hashcore", env="HASHCORE_PATH")
    
    # Configurações de thresholds
    temp_max: float = Field(default=80.0, env="TEMP_MAX")
    temp_critical: float = Field(default=85.0, env="TEMP_CRITICAL")
    humidity_max: float = Field(default=80.0, env="HUMIDITY_MAX")
    dewpoint_diff: float = Field(default=2.0, env="DEWPOINT_DIFF")
    
    # Configurações de eficiência
    efficiency_min: float = Field(default=0.8, env="EFFICIENCY_MIN")
    hashrate_min: float = Field(default=0.9, env="HASHRATE_MIN")
    
    # Configurações de rede
    connection_timeout: int = Field(default=30, env="CONNECTION_TIMEOUT")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    
    # Configurações de logs
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="bitcoin_mining.log", env="LOG_FILE")
    
    # Configurações de backup
    backup_interval: int = Field(default=3600, env="BACKUP_INTERVAL")  # segundos
    backup_retention_days: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_device_config()
    
    def _load_device_config(self):
        """Carregar configurações específicas de dispositivos"""
        config_path = Path("config/devices.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.device_config = yaml.safe_load(f)
        else:
            self.device_config = self._get_default_device_config()
    
    def _get_default_device_config(self) -> Dict[str, Any]:
        """Configuração padrão de dispositivos"""
        return {
            "abb": {
                "host": self.abb_host,
                "port": self.abb_port,
                "slave_id": 1,
                "registers": {
                    "voltage": 0,
                    "current": 2,
                    "power": 4,
                    "frequency": 6,
                    "energy": 8
                }
            },
            "ble": {
                "interface": self.ble_interface,
                "baudrate": 9600,
                "timeout": 5,
                "retry_attempts": 3
            },
            "asic": {
                "hashcore_path": self.hashcore_path,
                "timeout": self.asic_timeout,
                "retry_attempts": self.asic_retry_attempts,
                "discovery_interval": 60
            },
            "sensors": {
                "temperature": {
                    "min": -40,
                    "max": 125,
                    "critical": self.temp_critical,
                    "warning": self.temp_max
                },
                "humidity": {
                    "min": 0,
                    "max": 100,
                    "critical": 90,
                    "warning": self.humidity_max
                }
            }
        }
    
    def get_device_config(self, device_type: str) -> Dict[str, Any]:
        """Obter configuração de um tipo de dispositivo"""
        return self.device_config.get(device_type, {})
    
    def get_thresholds(self) -> Dict[str, float]:
        """Obter thresholds configurados"""
        return {
            "temp_max": self.temp_max,
            "temp_critical": self.temp_critical,
            "humidity_max": self.humidity_max,
            "dewpoint_diff": self.dewpoint_diff,
            "efficiency_min": self.efficiency_min,
            "hashrate_min": self.hashrate_min
        }
    
    def is_llm_configured(self) -> bool:
        """Verificar se LLM está configurado"""
        if self.llm_mode == "disabled":
            return False
        if self.llm_mode == "local":
            return bool(self.llm_endpoint)
        if self.llm_mode == "remote":
            return bool(self.openai_api_key or self.anthropic_api_key)
        return False
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Obter configuração do LLM"""
        return {
            "mode": self.llm_mode,
            "endpoint": self.llm_endpoint,
            "openai_api_key": self.openai_api_key,
            "anthropic_api_key": self.anthropic_api_key
        }
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Obter configuração de notificações"""
        return {
            "whatsapp_token": self.whatsapp_token,
            "telegram_bot_token": self.telegram_bot_token,
            "smtp": {
                "host": self.smtp_host,
                "port": self.smtp_port,
                "user": self.smtp_user,
                "password": self.smtp_pass
            }
        }
    
    def validate_config(self) -> bool:
        """Validar configuração"""
        errors = []
        
        # Validar URLs
        if not self.database_url.startswith(("postgresql://", "sqlite://")):
            errors.append("DATABASE_URL deve ser uma URL válida do PostgreSQL ou SQLite")
        
        if not self.redis_url.startswith("redis://"):
            errors.append("REDIS_URL deve ser uma URL válida do Redis")
        
        # Validar configurações de LLM
        if self.llm_mode != "disabled" and not self.is_llm_configured():
            errors.append("LLM não está configurado corretamente")
        
        # Validar thresholds
        if self.temp_critical <= self.temp_max:
            errors.append("TEMP_CRITICAL deve ser maior que TEMP_MAX")
        
        if self.efficiency_min < 0 or self.efficiency_min > 1:
            errors.append("EFFICIENCY_MIN deve estar entre 0 e 1")
        
        if errors:
            for error in errors:
                print(f"❌ Erro de configuração: {error}")
            return False
        
        return True

# Instância global da configuração
config = Config()


