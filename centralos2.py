#!/usr/bin/env python3
"""CentralOS2 – plataforma unificada de automação para mineração
=================================================================

Este script implementa uma versão moderna do *CentralOS2*,
reaproveitando a arquitetura presente em ``bitcoin_mining_automation``
e mantendo os principais fluxos operacionais do script original.

Principais características
-------------------------
* **Configuração unificada** – Lê ``.env`` e ``config/devices.yaml`` da
  pasta ``bitcoin_mining_automation`` quando disponível.
* **Monitoramento em camadas** – Loops assíncronos obtêm informações do
  inversor/ABB (Modbus), sensores BLE Xiaomi (quando suportado), ASICs e
  API da F2Pool.
* **Automação inteligente** – Regras de segurança e rotinas
  programadas, inspiradas nos scripts da pasta
  ``bitcoin_mining_automation``.
* **Interface de terminal** – Console interativo que funciona bem em
  uma Raspberry Pi sem ambiente gráfico.
* **Persistência** – Salvamento de ASICs, rotinas e CSVs de histórico
  em ``~/.centralos2``.

O foco é oferecer uma base estável para uso em Raspberry Pi, com
tratamento de falhas e dependências opcionais. Todas as integrações são
projetadas para falhar em modo "simulado" quando bibliotecas ou
hardware não estiverem disponíveis, permitindo testes em qualquer
ambiente.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import math
import signal
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # ``schedule`` é usado tanto aqui quanto no projeto de automação
    import schedule
except Exception:  # pragma: no cover - fallback simplificado
    schedule = None  # type: ignore

try:
    import yaml
except Exception:  # pragma: no cover - fallback simples
    yaml = None

# ---------------------------------------------------------------------------
# Integração com ``bitcoin_mining_automation``
# ---------------------------------------------------------------------------
ROOT_PATH = Path(__file__).resolve().parent
BACKEND_PATH = ROOT_PATH / "bitcoin_mining_automation" / "backend"
if BACKEND_PATH.exists():
    sys.path.insert(0, str(BACKEND_PATH))

try:
    from core.config import Config as AutomationConfig  # type: ignore
except Exception:  # pragma: no cover - dependência opcional
    AutomationConfig = None  # type: ignore

try:  # Dependência opcional para Modbus
    from pymodbus.client import ModbusTcpClient
except Exception:  # pragma: no cover - permite modo simulado
    ModbusTcpClient = None  # type: ignore

try:  # BLE opcional
    from bleak import BleakScanner
    from atc_mi_interface import atc_mi_advertising_format
except Exception:  # pragma: no cover - sensores BLE são opcionais
    BleakScanner = None  # type: ignore
    atc_mi_advertising_format = None  # type: ignore

try:  # HTTP
    import requests
except Exception as exc:  # pragma: no cover
    raise RuntimeError("A biblioteca 'requests' é obrigatória.") from exc

# ---------------------------------------------------------------------------
# Configuração e utilidades
# ---------------------------------------------------------------------------
@dataclass
class SimpleConfig:
    """Configuração mínima utilizada quando o ``Config`` do backend não
    estiver disponível.
    """

    abb_host: str = "192.168.0.111"
    abb_port: int = 502
    abb_slave_id: int = 1
    abb_registers: Dict[str, int] = field(
        default_factory=lambda: {
            "speed": 685,
            "command": 684,
            "frequency": 5,
            "current": 3,
            "temperature": 30,
            "state": 6,
            "potenciometer": 100,
        }
    )
    multimeter_host: str = "192.168.0.108"
    multimeter_port: int = 503
    multimeter_registers: Dict[str, int] = field(
        default_factory=lambda: {
            "voltage_l1": 12288,
            "voltage_l2": 12290,
            "voltage_l3": 12292,
            "current_l1": 12304,
            "current_l2": 12306,
            "current_l3": 12308,
            "active_power": 12322,
            "frequency": 12366,
            "active_energy": 12410,
        }
    )
    pool_url: str = "https://api.f2pool.com"
    f2pool_api_token: Optional[str] = None
    mining_user: str = ""
    csv_dir: Path = Path.home() / ".centralos2" / "csv"
    log_file: Path = Path.home() / ".centralos2" / "centralos2.log"
    collection_interval: int = 10
    humidity_max: float = 90.0
    dewpoint_diff_min: float = 4.0
    whatsapp_token: Optional[str] = None

    def get_device_config(self, device_type: str) -> Dict[str, Any]:
        if device_type == "abb":
            return {
                "host": self.abb_host,
                "port": self.abb_port,
                "slave_id": self.abb_slave_id,
                "registers": self.abb_registers,
            }
        if device_type == "multimeter":
            return {
                "host": self.multimeter_host,
                "port": self.multimeter_port,
                "slave_id": 1,
                "registers": self.multimeter_registers,
            }
        return {}


def ensure_directories(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_config() -> SimpleConfig:
    """Carrega a configuração do sistema.

    Prioriza ``AutomationConfig`` do backend; quando não disponível,
    utiliza :class:`SimpleConfig`.
    """

    data_dir = Path.home() / ".centralos2"
    ensure_directories(data_dir)
    ensure_directories(data_dir / "csv")

    if AutomationConfig is not None:
        try:
            config = AutomationConfig()
            cfg = SimpleConfig()
            cfg.abb_host = config.abb_host
            cfg.abb_port = config.abb_port
            cfg.abb_slave_id = config.get_device_config("abb").get("slave_id", 1)
            cfg.abb_registers.update(
                config.get_device_config("abb").get("registers", {})
            )
            mult = config.get_device_config("multimeter") or {}
            cfg.multimeter_host = mult.get("host", cfg.multimeter_host)
            cfg.multimeter_port = mult.get("port", cfg.multimeter_port)
            cfg.multimeter_registers.update(mult.get("registers", {}))
            cfg.pool_url = config.pool_url.rstrip("/")
            cfg.f2pool_api_token = config.f2pool_api_token
            cfg.mining_user = config.dict().get("mining_user_name", "") or ""
            cfg.collection_interval = config.collection_interval
            cfg.humidity_max = config.humidity_max
            cfg.dewpoint_diff_min = config.dewpoint_diff
            cfg.whatsapp_token = config.whatsapp_token
            cfg.csv_dir = data_dir / "csv"
            cfg.log_file = data_dir / "centralos2.log"
            return cfg
        except Exception as exc:  # pragma: no cover - fallback simples
            logging.getLogger("centralos2").warning(
                "Falha ao carregar Config do backend (%s). Usando SimpleConfig.",
                exc,
            )
    cfg = SimpleConfig()
    cfg.csv_dir = data_dir / "csv"
    cfg.log_file = data_dir / "centralos2.log"
    devices_cfg = load_yaml(BACKEND_PATH.parent / "config" / "devices.yaml")
    if devices_cfg:
        abb_cfg = devices_cfg.get("abb", {})
        cfg.abb_host = abb_cfg.get("host", cfg.abb_host)
        cfg.abb_port = abb_cfg.get("port", cfg.abb_port)
        cfg.abb_registers.update(abb_cfg.get("registers", {}))
        mult = devices_cfg.get("multimeter", {})
        cfg.multimeter_host = mult.get("host", cfg.multimeter_host)
        cfg.multimeter_port = mult.get("port", cfg.multimeter_port)
        cfg.multimeter_registers.update(mult.get("registers", {}))
    return cfg


# ---------------------------------------------------------------------------
# Componentes de hardware e integrações
# ---------------------------------------------------------------------------
@dataclass
class ExhaustState:
    speed: int = 0
    frequency: float = 0.0
    current: float = 0.0
    temperature: float = 0.0
    running: bool = False


class ExhaustFanController:
    """Controla o inversor/ventilador via Modbus TCP.

    Quando ``pymodbus`` não está disponível a classe opera em modo
    simulado, permitindo testes sem hardware.
    """

    def __init__(self, config: SimpleConfig):
        registers = config.get_device_config("abb").get("registers", {})
        self.host = config.abb_host
        self.port = config.abb_port
        self.slave_id = config.get_device_config("abb").get("slave_id", 1)
        self.speed_register = int(registers.get("speed", 685))
        self.command_register = int(registers.get("command", 684))
        self.frequency_register = int(registers.get("frequency", 5))
        self.current_register = int(registers.get("current", 3))
        self.temperature_register = int(registers.get("temperature", 30))
        self.state_register = int(registers.get("state", 6))
        self.simulated = ModbusTcpClient is None
        self._state = ExhaustState()
        self._lock = asyncio.Lock()

    async def set_speed(self, value: int) -> ExhaustState:
        value = max(0, min(100, int(value)))
        async with self._lock:
            if self.simulated:
                self._state.speed = value
                return self._state
            return await asyncio.to_thread(self._set_speed_sync, value)

    def _set_speed_sync(self, value: int) -> ExhaustState:
        assert ModbusTcpClient is not None
        client = ModbusTcpClient(host=self.host, port=self.port, timeout=3)
        try:
            if not client.connect():
                raise ConnectionError("Falha ao conectar ao inversor")
            register_value = int((value / 100.0) * 9999)
            client.write_register(self.speed_register, register_value, unit=self.slave_id)
            self._state.speed = value
            return self._state
        finally:
            client.close()

    async def command(self, action: str) -> ExhaustState:
        action = action.lower()
        async with self._lock:
            if self.simulated:
                self._state.running = action in {"start", "resume", "on"}
                return self._state
            return await asyncio.to_thread(self._command_sync, action)

    def _command_sync(self, action: str) -> ExhaustState:
        assert ModbusTcpClient is not None
        value = 0x0007 if action in {"start", "resume", "on"} else 0x0000
        client = ModbusTcpClient(host=self.host, port=self.port, timeout=3)
        try:
            if not client.connect():
                raise ConnectionError("Falha ao conectar ao inversor")
            client.write_register(self.command_register, value, unit=self.slave_id)
            self._state.running = value == 0x0007
            return self._state
        finally:
            client.close()

    async def read_state(self) -> ExhaustState:
        async with self._lock:
            if self.simulated:
                return self._state
            return await asyncio.to_thread(self._read_state_sync)

    def _read_state_sync(self) -> ExhaustState:
        assert ModbusTcpClient is not None
        client = ModbusTcpClient(host=self.host, port=self.port, timeout=3)
        try:
            if not client.connect():
                raise ConnectionError("Falha ao conectar ao inversor")
            freq = client.read_holding_registers(self.frequency_register, 1, unit=self.slave_id)
            current = client.read_holding_registers(self.current_register, 1, unit=self.slave_id)
            temp = client.read_holding_registers(self.temperature_register, 1, unit=self.slave_id)
            state = client.read_holding_registers(self.state_register, 1, unit=self.slave_id)
            if freq.isError():
                raise ConnectionError("Não foi possível ler registradores do inversor")
            self._state.frequency = freq.registers[0] / 10.0
            if not current.isError():
                self._state.current = current.registers[0] / 10.0
            if not temp.isError():
                self._state.temperature = temp.registers[0] / 10.0
            if not state.isError():
                self._state.running = state.registers[0] == 1
            return self._state
        finally:
            client.close()


@dataclass
class MultimeterSample:
    timestamp: datetime
    voltage_l1: float
    voltage_l2: float
    voltage_l3: float
    current_l1: float
    current_l2: float
    current_l3: float
    active_power: float
    frequency: float
    active_energy: float


class ABBMultimeter:
    def __init__(self, config: SimpleConfig):
        registers = config.get_device_config("multimeter").get("registers", {})
        self.host = config.multimeter_host
        self.port = config.multimeter_port
        self.slave_id = config.get_device_config("multimeter").get("slave_id", 1)
        self.registers = registers
        self.simulated = ModbusTcpClient is None

    async def read_sample(self) -> Optional[MultimeterSample]:
        if self.simulated:
            now = datetime.utcnow()
            return MultimeterSample(
                timestamp=now,
                voltage_l1=220.0,
                voltage_l2=221.0,
                voltage_l3=219.0,
                current_l1=12.5,
                current_l2=12.4,
                current_l3=12.7,
                active_power=8400.0,
                frequency=59.9,
                active_energy=12345.6,
            )
        return await asyncio.to_thread(self._read_sample_sync)

    def _read_sample_sync(self) -> Optional[MultimeterSample]:
        assert ModbusTcpClient is not None
        client = ModbusTcpClient(host=self.host, port=self.port, timeout=3)
        try:
            if not client.connect():
                raise ConnectionError("Falha ao conectar ao multimedidor ABB")
            def _read_float(address: int) -> float:
                resp = client.read_holding_registers(address, 2, unit=self.slave_id)
                if resp.isError():
                    raise ConnectionError(f"Falha ao ler registro {address}")
                high, low = resp.registers
                raw = (high << 16) | low
                if raw & (1 << 31):  # sinal negativo
                    raw -= 1 << 32
                return raw / 100.0
            return MultimeterSample(
                timestamp=datetime.utcnow(),
                voltage_l1=_read_float(self.registers.get("voltage_l1", 12288)),
                voltage_l2=_read_float(self.registers.get("voltage_l2", 12290)),
                voltage_l3=_read_float(self.registers.get("voltage_l3", 12292)),
                current_l1=_read_float(self.registers.get("current_l1", 12304)),
                current_l2=_read_float(self.registers.get("current_l2", 12306)),
                current_l3=_read_float(self.registers.get("current_l3", 12308)),
                active_power=_read_float(self.registers.get("active_power", 12322)),
                frequency=_read_float(self.registers.get("frequency", 12366)),
                active_energy=_read_float(self.registers.get("active_energy", 12410)),
            )
        finally:
            client.close()


@dataclass
class ASIC:
    ip: str
    token: str
    last_state: str = "unknown"
    last_hashrate: float = 0.0
    last_seen: Optional[datetime] = None


class ASICManager:
    STORAGE_FILE = Path.home() / ".centralos2" / "asics.json"

    def __init__(self):
        self._session = requests.Session()
        self._lock = asyncio.Lock()
        self.asics: List[ASIC] = []
        ensure_directories(self.STORAGE_FILE.parent)
        self._load()

    # ------------------------------- Persistência -----------------------
    def _load(self) -> None:
        if not self.STORAGE_FILE.exists():
            self.asics = []
            return
        try:
            data = json.loads(self.STORAGE_FILE.read_text("utf-8"))
        except json.JSONDecodeError:
            data = []
        self.asics = [ASIC(**entry) for entry in data]

    def _save(self) -> None:
        payload = [
            {
                "ip": a.ip,
                "token": a.token,
                "last_state": a.last_state,
                "last_hashrate": a.last_hashrate,
                "last_seen": a.last_seen.isoformat() if a.last_seen else None,
            }
            for a in self.asics
        ]
        self.STORAGE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # ------------------------------- CRUD --------------------------------
    def add(self, ip: str, token: str) -> None:
        if any(a.ip == ip for a in self.asics):
            raise ValueError(f"ASIC {ip} já cadastrada")
        self.asics.append(ASIC(ip=ip, token=token))
        self._save()

    def remove(self, ip: str) -> None:
        self.asics = [a for a in self.asics if a.ip != ip]
        self._save()

    def list(self) -> List[ASIC]:
        return list(self.asics)

    # ------------------------------- Monitoramento ----------------------
    async def refresh_status(self) -> None:
        async with self._lock:
            tasks = [asyncio.to_thread(self._fetch_status, asic) for asic in self.asics]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                self._save()

    def _fetch_status(self, asic: ASIC) -> None:
        url = f"http://{asic.ip}/api/v1/status"
        headers = {"Authorization": f"Bearer {asic.token}"}
        try:
            response = self._session.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"HTTP {response.status_code}")
            data = response.json()
            asic.last_state = data.get("miner_state", "unknown")
            asic.last_hashrate = data.get("hashrate", 0.0)
            asic.last_seen = datetime.utcnow()
        except Exception as exc:
            asic.last_state = f"offline ({exc})"

    async def command(self, ip: str, action: str) -> None:
        asic = next((a for a in self.asics if a.ip == ip), None)
        if not asic:
            raise ValueError(f"ASIC {ip} não encontrada")
        await asyncio.to_thread(self._send_command, asic, action)

    async def broadcast(self, action: str) -> None:
        tasks = [asyncio.to_thread(self._send_command, a, action) for a in self.asics]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _send_command(self, asic: ASIC, action: str) -> None:
        endpoints = {"sleep": "stop", "resume": "start"}
        endpoint = endpoints.get(action)
        if not endpoint:
            raise ValueError(f"Ação inválida: {action}")
        url = f"http://{asic.ip}/api/v1/mining/{endpoint}"
        headers = {"Authorization": f"Bearer {asic.token}"}
        response = self._session.post(url, headers=headers, json={}, timeout=5)
        if response.status_code != 200:
            raise ConnectionError(f"Falha HTTP {response.status_code}")


class F2PoolClient:
    def __init__(self, config: SimpleConfig):
        self.base_url = config.pool_url.rstrip("/")
        self.api_token = config.f2pool_api_token
        self.user = config.mining_user
        self.session = requests.Session()

    async def fetch_overview(self) -> Dict[str, Any]:
        if not self.api_token or not self.user:
            return {}
        headers = {"Content-Type": "application/json", "F2P-API-SECRET": self.api_token}
        payload = {"mining_user_name": self.user, "currency": "bitcoin"}
        info_url = f"{self.base_url}/v2/hash_rate/info"
        workers_url = f"{self.base_url}/v2/hash_rate/worker/list"
        info, workers = await asyncio.gather(
            asyncio.to_thread(self._post_json, info_url, headers, payload),
            asyncio.to_thread(self._post_json, workers_url, headers, payload),
        )
        return {"info": info, "workers": workers}

    def _post_json(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Any:
        response = self.session.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code != 200:
            raise ConnectionError(f"F2Pool HTTP {response.status_code}")
        return response.json()


class BLEMonitor:
    def __init__(self):
        self.enabled = BleakScanner is not None and atc_mi_advertising_format is not None
        self.sensors: Dict[str, Dict[str, float]] = {}

    async def scan(self) -> Dict[str, Dict[str, float]]:
        if not self.enabled:
            return self.sensors
        devices = await BleakScanner.discover(timeout=5.0)
        for device in devices:
            if not device.metadata.get("manufacturer_data"):
                continue
            for _, payload in device.metadata["manufacturer_data"].items():
                try:
                    parsed = atc_mi_advertising_format(payload)
                except Exception:
                    continue
                temp = parsed.get("temperature")
                hum = parsed.get("humidity")
                if temp is None or hum is None:
                    continue
                dew = calculate_dew_point(temp, hum)
                self.sensors[device.address] = {
                    "temperature": float(temp),
                    "humidity": float(hum),
                    "dew_point": float(dew) if dew is not None else None,
                }
        return self.sensors


# ---------------------------------------------------------------------------
# Funções utilitárias e automação
# ---------------------------------------------------------------------------
def calculate_dew_point(temperature: float, humidity: float) -> Optional[float]:
    try:
        a, b = 17.27, 237.7
        gamma = (a * temperature) / (b + temperature) + math.log(humidity / 100.0)
        return (b * gamma) / (a - gamma)
    except Exception:  # pragma: no cover - valores inválidos
        return None


def format_status_table(rows: Iterable[Tuple[str, str]]) -> str:
    max_key = max((len(key) for key, _ in rows), default=0)
    return "\n".join(f"{key:<{max_key}} : {value}" for key, value in rows)


class AutomationEngine:
    def __init__(self, config: SimpleConfig, asic_manager: ASICManager, fan: ExhaustFanController):
        self.config = config
        self.asic_manager = asic_manager
        self.fan = fan

    async def evaluate(self, state: Dict[str, Any]) -> List[str]:
        actions = []
        humidity = state.get("environment", {}).get("humidity")
        dew = state.get("environment", {}).get("dew_point")
        inverter_running = state.get("exhaust", {}).get("running", False)
        miners_active = any(a.last_state.lower() == "mining" for a in self.asic_manager.list())

        if not inverter_running and miners_active:
            await self.asic_manager.broadcast("sleep")
            actions.append("ASICs colocadas em sleep (inversor parado)")

        if humidity is not None and humidity >= self.config.humidity_max:
            await self.fan.set_speed(20)
            actions.append("Umidade alta – exaustor ajustado para 20%")

        if humidity is not None and dew is not None:
            ambient = state.get("environment", {}).get("temperature")
            if ambient is not None and ambient - dew < self.config.dewpoint_diff_min:
                await self.fan.set_speed(10)
                actions.append("Ponto de orvalho próximo – exaustor ajustado para 10%")
        return actions


class RoutineScheduler:
    STORAGE_FILE = Path.home() / ".centralos2" / "rotinas_automacao.json"

    def __init__(self, asic_manager: ASICManager, fan: ExhaustFanController):
        self.asic_manager = asic_manager
        self.fan = fan
        self._routines: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        ensure_directories(self.STORAGE_FILE.parent)
        if not self.STORAGE_FILE.exists():
            self.STORAGE_FILE.write_text("[]", encoding="utf-8")
        data = json.loads(self.STORAGE_FILE.read_text("utf-8"))
        self._routines = data
        self._install_jobs()

    def _save(self) -> None:
        self.STORAGE_FILE.write_text(json.dumps(self._routines, indent=2), encoding="utf-8")

    def _install_jobs(self) -> None:
        if schedule is None:
            return
        schedule.clear("centralos2")
        for routine in self._routines:
            days = routine.get("days", []) or ["daily"]
            time_str = routine.get("time", "00:00")
            for day in days:
                job = getattr(schedule.every(), day.lower(), schedule.every())
                job = job.at(time_str)
                job.do(self._execute_routine, routine).tag("centralos2")

    def _execute_routine(self, routine: Dict[str, Any]) -> None:
        speed = int(routine.get("speed", 100))
        action = routine.get("action", "resume")
        asyncio.create_task(self.fan.set_speed(speed))
        if action in {"sleep", "resume"}:
            coro = self.asic_manager.broadcast("sleep" if action == "sleep" else "resume")
            asyncio.create_task(coro)

    async def tick(self) -> None:
        if schedule is None:
            return
        schedule.run_pending()

    def list(self) -> List[Dict[str, Any]]:
        return list(self._routines)

    def add(self, routine: Dict[str, Any]) -> None:
        self._routines.append(routine)
        self._save()
        self._install_jobs()

    def remove(self, index: int) -> None:
        if 0 <= index < len(self._routines):
            self._routines.pop(index)
            self._save()
            self._install_jobs()
        else:
            raise IndexError("Índice de rotina inválido")


# ---------------------------------------------------------------------------
# Núcleo principal da aplicação
# ---------------------------------------------------------------------------
class CentralOS2App:
    def __init__(self, config: SimpleConfig, interactive: bool = True, print_interval: int = 10):
        self.config = config
        self.interactive = interactive
        self.print_interval = max(3, print_interval)
        self.fan = ExhaustFanController(config)
        self.multimeter = ABBMultimeter(config)
        self.asic_manager = ASICManager()
        self.pool_client = F2PoolClient(config)
        self.ble_monitor = BLEMonitor()
        self.automation = AutomationEngine(config, self.asic_manager, self.fan)
        self.scheduler = RoutineScheduler(self.asic_manager, self.fan)
        self.state: Dict[str, Any] = {
            "exhaust": {},
            "multimeter": {},
            "pool": {},
            "environment": {},
            "automation": {"last_actions": []},
        }
        self._shutdown = asyncio.Event()
        self._print_task: Optional[asyncio.Task] = None
        self._csv_file = config.csv_dir / "multimeter.csv"

    # -------------------------- Inicialização e ciclo -------------------
    async def start(self) -> None:
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        await self._ensure_csv_headers()
        tasks = [
            asyncio.create_task(self._update_exhaust_loop()),
            asyncio.create_task(self._update_multimeter_loop()),
            asyncio.create_task(self._update_pool_loop()),
            asyncio.create_task(self._update_ble_loop()),
            asyncio.create_task(self._automation_loop()),
            asyncio.create_task(self._scheduler_loop()),
        ]
        if self.interactive:
            tasks.append(asyncio.create_task(self._command_loop()))
            self._print_task = asyncio.create_task(self._print_loop())
        await self._shutdown.wait()
        for task in tasks:
            task.cancel()
        if self._print_task:
            self._print_task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if self._print_task:
            await asyncio.gather(self._print_task, return_exceptions=True)

    def _handle_signal(self, signum, frame) -> None:  # pragma: no cover - sinal
        logging.info("Sinal %s recebido – finalizando...", signum)
        self._shutdown.set()

    async def _ensure_csv_headers(self) -> None:
        ensure_directories(self.config.csv_dir)
        if not self._csv_file.exists():
            with self._csv_file.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "timestamp",
                        "voltage_l1",
                        "voltage_l2",
                        "voltage_l3",
                        "current_l1",
                        "current_l2",
                        "current_l3",
                        "active_power",
                        "frequency",
                        "active_energy",
                    ]
                )

    # -------------------------- Loops periódicos ------------------------
    async def _update_exhaust_loop(self) -> None:
        while not self._shutdown.is_set():
            try:
                state = await self.fan.read_state()
                self.state["exhaust"] = {
                    "speed": state.speed,
                    "frequency": state.frequency,
                    "current": state.current,
                    "temperature": state.temperature,
                    "running": state.running,
                }
            except Exception as exc:
                logging.warning("Falha ao ler inversor: %s", exc)
            await asyncio.sleep(self.config.collection_interval)

    async def _update_multimeter_loop(self) -> None:
        while not self._shutdown.is_set():
            try:
                sample = await self.multimeter.read_sample()
                if sample:
                    self.state["multimeter"] = sample.__dict__
                    await asyncio.to_thread(self._append_csv, sample)
            except Exception as exc:
                logging.warning("Falha ao ler multimedidor: %s", exc)
            await asyncio.sleep(self.config.collection_interval)

    def _append_csv(self, sample: MultimeterSample) -> None:
        with self._csv_file.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    sample.timestamp.isoformat(),
                    sample.voltage_l1,
                    sample.voltage_l2,
                    sample.voltage_l3,
                    sample.current_l1,
                    sample.current_l2,
                    sample.current_l3,
                    sample.active_power,
                    sample.frequency,
                    sample.active_energy,
                ]
            )

    async def _update_pool_loop(self) -> None:
        while not self._shutdown.is_set():
            try:
                overview = await self.pool_client.fetch_overview()
                if overview:
                    self.state["pool"] = overview
            except Exception as exc:
                logging.warning("Falha ao consultar F2Pool: %s", exc)
            await asyncio.sleep(max(self.config.collection_interval * 3, 30))

    async def _update_ble_loop(self) -> None:
        if not self.ble_monitor.enabled:
            return
        while not self._shutdown.is_set():
            try:
                sensors = await self.ble_monitor.scan()
                if sensors:
                    averages = self._aggregate_environment(sensors)
                    self.state["environment"] = averages
            except Exception as exc:
                logging.warning("Falha ao ler sensores BLE: %s", exc)
            await asyncio.sleep(max(self.config.collection_interval, 30))

    def _aggregate_environment(self, sensors: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        if not sensors:
            return {}
        temp_vals = [data.get("temperature") for data in sensors.values() if data.get("temperature") is not None]
        hum_vals = [data.get("humidity") for data in sensors.values() if data.get("humidity") is not None]
        dew_vals = [data.get("dew_point") for data in sensors.values() if data.get("dew_point") is not None]
        def _avg(values: List[Optional[float]]) -> Optional[float]:
            clean = [float(v) for v in values if v is not None]
            if not clean:
                return None
            return sum(clean) / len(clean)
        return {
            "temperature": _avg(temp_vals),
            "humidity": _avg(hum_vals),
            "dew_point": _avg(dew_vals),
        }

    async def _automation_loop(self) -> None:
        while not self._shutdown.is_set():
            try:
                await self.asic_manager.refresh_status()
                actions = await self.automation.evaluate(self.state)
                if actions:
                    self.state.setdefault("automation", {})["last_actions"] = actions
                    for action in actions:
                        logging.info("Automação: %s", action)
            except Exception as exc:
                logging.warning("Falha na automação: %s", exc)
            await asyncio.sleep(max(self.config.collection_interval, 30))

    async def _scheduler_loop(self) -> None:
        while not self._shutdown.is_set():
            try:
                await self.scheduler.tick()
            except Exception as exc:
                logging.warning("Erro no agendador: %s", exc)
            await asyncio.sleep(30)

    async def _print_loop(self) -> None:
        while not self._shutdown.is_set():
            await asyncio.sleep(self.print_interval)
            print("\n" + self.render_status() + "\n", flush=True)

    # -------------------------- Interface interativa --------------------
    async def _command_loop(self) -> None:
        help_text = textwrap.dedent(
            """
            Comandos disponíveis:
              status                      → mostra o estado atual
              fan set <0-100>             → ajusta velocidade do exaustor
              fan on|off                  → liga/desliga o exaustor
              asic list                   → lista ASICs cadastradas
              asic add <ip> <token>       → adiciona ASIC
              asic remove <ip>            → remove ASIC
              asic sleep|resume [ip]      → sleep/resume em uma ASIC ou em todas
              routine list                → lista rotinas
              routine add <HH:MM> <speed> <sleep|resume>
                                        → adiciona rotina diária
              routine del <index>         → remove rotina por índice
              quit                        → encerra o sistema
            """
        ).strip()
        print(help_text, flush=True)
        while not self._shutdown.is_set():
            try:
                command = await asyncio.to_thread(input, "centralos2> ")
            except (EOFError, KeyboardInterrupt):
                self._shutdown.set()
                break
            command = command.strip()
            if not command:
                continue
            try:
                if command in {"quit", "exit"}:
                    self._shutdown.set()
                    break
                await self._execute_command(command)
            except Exception as exc:
                print(f"Erro: {exc}", flush=True)

    async def _execute_command(self, command: str) -> None:
        tokens = command.split()
        if tokens[0] == "status":
            print(self.render_status(), flush=True)
        elif tokens[0] == "fan" and len(tokens) >= 2:
            if tokens[1] == "set" and len(tokens) == 3:
                await self.fan.set_speed(int(tokens[2]))
            elif tokens[1] in {"on", "off"}:
                await self.fan.command("start" if tokens[1] == "on" else "stop")
            else:
                raise ValueError("Uso: fan set <0-100> | fan on | fan off")
        elif tokens[0] == "asic" and len(tokens) >= 2:
            await self._handle_asic_command(tokens[1:])
        elif tokens[0] == "routine" and len(tokens) >= 2:
            self._handle_routine_command(tokens[1:])
        else:
            print("Comando desconhecido. Digite 'status' ou 'quit'.", flush=True)

    async def _handle_asic_command(self, tokens: List[str]) -> None:
        sub = tokens[0]
        if sub == "list":
            rows = []
            for idx, asic in enumerate(self.asic_manager.list()):
                rows.append(
                    f"[{idx}] {asic.ip} | {asic.last_state} | hashrate: {asic.last_hashrate} | "
                    f"seen: {asic.last_seen}"
                )
            print("\n".join(rows) if rows else "Nenhuma ASIC cadastrada.", flush=True)
        elif sub == "add" and len(tokens) == 3:
            self.asic_manager.add(tokens[1], tokens[2])
            print("ASIC adicionada.", flush=True)
        elif sub == "remove" and len(tokens) == 2:
            self.asic_manager.remove(tokens[1])
            print("ASIC removida.", flush=True)
        elif sub in {"sleep", "resume"}:
            if len(tokens) == 2:
                await self.asic_manager.command(tokens[1], sub)
            else:
                await self.asic_manager.broadcast(sub)
            print("Comando enviado.", flush=True)
        else:
            raise ValueError(
                "Uso: asic list | asic add <ip> <token> | asic remove <ip> | "
                "asic sleep [ip] | asic resume [ip]"
            )

    def _handle_routine_command(self, tokens: List[str]) -> None:
        sub = tokens[0]
        if sub == "list":
            routines = self.scheduler.list()
            if not routines:
                print("Nenhuma rotina cadastrada.", flush=True)
                return
            for idx, routine in enumerate(routines):
                print(f"[{idx}] {routine}", flush=True)
        elif sub == "add" and len(tokens) >= 4:
            routine = {
                "time": tokens[1],
                "speed": int(tokens[2]),
                "action": tokens[3],
                "days": ["daily"],
            }
            self.scheduler.add(routine)
            print("Rotina adicionada.", flush=True)
        elif sub == "del" and len(tokens) == 2:
            self.scheduler.remove(int(tokens[1]))
            print("Rotina removida.", flush=True)
        else:
            raise ValueError("Uso: routine list | routine add <HH:MM> <vel> <acao> | routine del <idx>")

    # -------------------------- Exibição de status ----------------------
    def render_status(self) -> str:
        exhaust = self.state.get("exhaust", {})
        mult = self.state.get("multimeter", {})
        env = self.state.get("environment", {})
        pool = self.state.get("pool", {})
        automation = self.state.get("automation", {})

        rows = [
            ("Exaustor", "Ligado" if exhaust.get("running") else "Desligado"),
            ("Velocidade", f"{exhaust.get('speed', 0)}%"),
            ("Frequência", f"{exhaust.get('frequency', '--')}")
        ]
        rows.append(("Corrente", f"{exhaust.get('current', '--')} A"))
        rows.append(("Temperatura", f"{exhaust.get('temperature', '--')} °C"))
        rows.append(("Potência ativa", f"{mult.get('active_power', '--')} W"))
        rows.append(("Energia ativa", f"{mult.get('active_energy', '--')} kWh"))
        rows.append(("Frequência rede", f"{mult.get('frequency', '--')} Hz"))

        if env:
            rows.append(("Temperatura ambiente", f"{env.get('temperature', '--')} °C"))
            rows.append(("Umidade", f"{env.get('humidity', '--')} %"))
            rows.append(("Ponto de orvalho", f"{env.get('dew_point', '--')} °C"))

        if pool:
            info = pool.get("info", {}).get("info", {})
            if info:
                hashrate = info.get("hash_rate")
                if hashrate is not None:
                    rows.append(("Hashrate", f"{hashrate / 1e12:.2f} TH/s"))
                h24 = info.get("h24_hash_rate")
                if h24 is not None:
                    rows.append(("Hashrate 24h", f"{h24 / 1e12:.2f} TH/s"))
            workers = pool.get("workers", {}).get("workers", [])
            if workers:
                active = sum(1 for w in workers if w.get("status") == 0)
                rows.append(("Workers", f"{active}/{len(workers)}"))

        actions = automation.get("last_actions", [])
        if actions:
            rows.append(("Últimas ações", "; ".join(actions)))
        return format_status_table(rows)


# ---------------------------------------------------------------------------
# Execução via CLI
# ---------------------------------------------------------------------------
def configure_logging(log_file: Path, verbose: bool = False) -> None:
    ensure_directories(log_file.parent)
    handlers = [logging.FileHandler(log_file, encoding="utf-8")]
    if verbose:
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CentralOS2 – automação de mineração")
    parser.add_argument("command", choices=["run", "status"], help="Ação principal")
    parser.add_argument("--verbose", action="store_true", help="Habilita logs no console")
    parser.add_argument(
        "--interval", type=int, default=10, help="Intervalo de atualização em segundos"
    )
    parser.add_argument(
        "--non-interactive", action="store_true", help="Executa sem console interativo"
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    config = load_config()
    configure_logging(config.log_file, verbose=args.verbose)
    logging.info("CentralOS2 iniciado (modo %s)", args.command)

    app = CentralOS2App(config, interactive=not args.non_interactive, print_interval=args.interval)

    if args.command == "status":
        print(app.render_status())
        return 0

    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:  # pragma: no cover
        logging.info("Execução interrompida pelo usuário")
    return 0


if __name__ == "__main__":
    sys.exit(main())
