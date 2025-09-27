"""BLE sensor collection."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

_LOGGER = logging.getLogger(__name__)


@dataclass
class BLESensorReading:
    device: str
    temperature: Optional[float]
    humidity: Optional[float]
    dew_point: Optional[float]


@dataclass
class BLEMonitor:
    devices: List[str]
    scan_interval: int = 60

    async def scan(self) -> List[BLESensorReading]:
        try:
            from bleak import BleakScanner
        except Exception:  # pragma: no cover - optional dependency
            _LOGGER.warning("Bleak not installed; skipping BLE scan")
            return []

        result: List[BLESensorReading] = []
        devices = await BleakScanner.discover(timeout=5.0)
        for device in devices:
            if self.devices and device.address not in self.devices:
                continue
            reading = self._parse(device.address, device.metadata or {})
            if reading:
                result.append(reading)
        return result

    def _parse(self, address: str, metadata: Dict) -> Optional[BLESensorReading]:
        manufacturer_data = metadata.get("manufacturer_data", {})
        if not manufacturer_data:
            return None
        value = next(iter(manufacturer_data.values()))
        if len(value) < 4:
            return None
        temp = value[0] / 2.0
        humidity = value[1]
        dew_point = temp - (100 - humidity) / 5.0
        return BLESensorReading(address, temp, humidity, dew_point)

    async def run(self):
        while True:
            readings = await self.scan()
            for reading in readings:
                _LOGGER.info(
                    "BLE %s temp=%.2fC humidity=%.2f%% dew_point=%.2fC",
                    reading.device,
                    reading.temperature or -1,
                    reading.humidity or -1,
                    reading.dew_point or -1,
                )
            await asyncio.sleep(self.scan_interval)
