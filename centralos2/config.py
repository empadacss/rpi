"""Configuration loading for CentralOS2."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class ModbusConfig:
    host: str
    port: int = 502
    unit_id: int = 1
    timeout: float = 3.0


@dataclass
class ABBConfig:
    host: str
    port: int = 503
    timeout: float = 3.0


@dataclass
class F2PoolConfig:
    user: str
    coin: str = "bitcoin"
    api_token: Optional[str] = None
    refresh_interval: int = 60


@dataclass
class BLEConfig:
    enabled: bool = True
    devices: List[str] = field(default_factory=list)
    scan_interval: int = 60


@dataclass
class DatabaseConfig:
    path: Path = Path("data/centralos.db")


@dataclass
class LoggingConfig:
    directory: Path = Path("logs")
    level: str = "INFO"
    max_bytes: int = 2 * 1024 * 1024
    backup_count: int = 5


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    max_tokens: int = 256
    temperature: float = 0.3
    enabled: bool = False


@dataclass
class AutomationRule:
    name: str
    enabled: bool = True
    parameters: dict = field(default_factory=dict)


@dataclass
class AutomationConfig:
    rules: List[AutomationRule] = field(default_factory=list)
    schedule_interval: int = 30


@dataclass
class ASICConfig:
    hosts: List[str] = field(default_factory=list)
    ssh_user: str = "root"
    ssh_password: Optional[str] = None


@dataclass
class SystemConfig:
    modbus: ModbusConfig
    abb: ABBConfig
    f2pool: F2PoolConfig
    ble: BLEConfig = field(default_factory=BLEConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    automation: AutomationConfig = field(default_factory=AutomationConfig)
    asic: ASICConfig = field(default_factory=ASICConfig)


def _coerce_path(value) -> Path:
    if isinstance(value, Path):
        return value
    return Path(value)


def load_config(path: Path | str) -> SystemConfig:
    """Load configuration from a YAML file."""
    path = Path(path)
    data = yaml.safe_load(path.read_text())

    modbus = ModbusConfig(**data.get("modbus", {}))
    abb = ABBConfig(**data.get("abb", {}))
    f2pool = F2PoolConfig(**data.get("f2pool", {}))

    ble = BLEConfig(**data.get("ble", {}))

    database_data = data.get("database", {})
    if "path" in database_data:
        database_data["path"] = _coerce_path(database_data["path"])
    database = DatabaseConfig(**database_data)

    logging_data = data.get("logging", {})
    if "directory" in logging_data:
        logging_data["directory"] = _coerce_path(logging_data["directory"])
    logging_cfg = LoggingConfig(**logging_data)

    llm_cfg = LLMConfig(**data.get("llm", {}))

    automation_rules = [AutomationRule(**rule) for rule in data.get("automation", {}).get("rules", [])]
    automation_cfg = AutomationConfig(
        rules=automation_rules,
        schedule_interval=data.get("automation", {}).get("schedule_interval", AutomationConfig().schedule_interval),
    )

    asic_cfg = ASICConfig(**data.get("asic", {}))

    return SystemConfig(
        modbus=modbus,
        abb=abb,
        f2pool=f2pool,
        ble=ble,
        database=database,
        logging=logging_cfg,
        llm=llm_cfg,
        automation=automation_cfg,
        asic=asic_cfg,
    )
