"""Modbus devices integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

from .config import ABBConfig, ModbusConfig

_LOGGER = logging.getLogger(__name__)


@dataclass
class InverterController:
    cfg: ModbusConfig

    def _client(self):
        from pymodbus.client import ModbusTcpClient  # type: ignore

        return ModbusTcpClient(host=self.cfg.host, port=self.cfg.port, timeout=self.cfg.timeout)

    def read_status(self) -> Dict[str, Optional[float]]:
        registers = {
            "frequency": 5,
            "current": 3,
            "temperature": 30,
            "state": 6,
            "speed": 685,
        }
        result: Dict[str, Optional[float]] = {}
        with self._client() as client:
            for key, address in registers.items():
                try:
                    response = client.read_holding_registers(address, 1, slave=self.cfg.unit_id)
                    if response.isError():  # type: ignore[attr-defined]
                        _LOGGER.warning("Error reading %s register %s: %s", key, address, response)
                        result[key] = None
                    else:
                        result[key] = float(response.registers[0])  # type: ignore[index]
                except Exception:  # pragma: no cover - hardware specific
                    _LOGGER.exception("Failed to read %s register", key)
                    result[key] = None
        return result

    def set_speed(self, speed: int) -> bool:
        with self._client() as client:
            try:
                response = client.write_register(685, speed, slave=self.cfg.unit_id)
                if response.isError():  # type: ignore[attr-defined]
                    _LOGGER.error("Failed to set inverter speed: %s", response)
                    return False
                _LOGGER.info("Inverter speed updated to %s", speed)
                return True
            except Exception:  # pragma: no cover - hardware specific
                _LOGGER.exception("Error writing inverter speed")
                return False

    def send_command(self, command: int) -> bool:
        with self._client() as client:
            try:
                response = client.write_register(684, command, slave=self.cfg.unit_id)
                if response.isError():  # type: ignore[attr-defined]
                    _LOGGER.error("Failed to send inverter command: %s", response)
                    return False
                _LOGGER.info("Inverter command %s sent", command)
                return True
            except Exception:  # pragma: no cover - hardware specific
                _LOGGER.exception("Error sending inverter command")
                return False

    def start(self) -> bool:
        return self.send_command(1)

    def stop(self) -> bool:
        return self.send_command(5)


@dataclass
class ABBCollector:
    cfg: ABBConfig

    def _client(self):
        from pymodbus.client import ModbusTcpClient  # type: ignore

        return ModbusTcpClient(host=self.cfg.host, port=self.cfg.port, timeout=self.cfg.timeout)

    def read_metrics(self) -> Dict[str, Optional[float]]:
        registers = {
            "voltage_l1": 12288,
            "voltage_l2": 12290,
            "voltage_l3": 12292,
            "current_l1": 12306,
            "current_l2": 12308,
            "current_l3": 12310,
            "active_power": 12224,
        }
        result: Dict[str, Optional[float]] = {}
        with self._client() as client:
            for key, address in registers.items():
                try:
                    response = client.read_input_registers(address, 2)
                    if response.isError():  # type: ignore[attr-defined]
                        _LOGGER.warning("Error reading ABB register %s", key)
                        result[key] = None
                    else:
                        # Convert two 16-bit registers into float by dividing by 10 for readability
                        value = response.registers[0]
                        result[key] = float(value) / 10.0
                except Exception:  # pragma: no cover - hardware specific
                    _LOGGER.exception("Failed to read ABB register %s", key)
                    result[key] = None
        return result
