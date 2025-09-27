"""Service orchestration for CentralOS."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from .asic import ASICFleet
from .automation import AutomationContext, AutomationEngine
from .ble import BLEMonitor, BLESensorReading
from .config import SystemConfig
from .database import Database
from .f2pool import F2PoolClient
from .llm import LLMBridge
from .logging_utils import configure_logging
from .modbus import ABBCollector, InverterController

_LOGGER = logging.getLogger(__name__)


@dataclass
class CentralOS:
    cfg: SystemConfig
    log_path: Optional[str] = None
    db: Database = field(init=False)
    inverter: InverterController = field(init=False)
    abb: ABBCollector = field(init=False)
    f2pool: F2PoolClient = field(init=False)
    asics: Optional[ASICFleet] = field(init=False, default=None)
    ble_monitor: Optional[BLEMonitor] = field(init=False, default=None)
    llm: Optional[LLMBridge] = field(init=False, default=None)
    automation: AutomationEngine = field(init=False)

    latest_inverter: dict = field(default_factory=dict, init=False)
    latest_sensors: List[BLESensorReading] = field(default_factory=list, init=False)
    latest_workers: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        log_path = configure_logging(self.cfg.logging)
        self.log_path = str(log_path)
        _LOGGER.info("CentralOS starting with configuration: %s", self.cfg)
        self.db = Database(self.cfg.database)
        self.db.initialise()
        self.inverter = InverterController(self.cfg.modbus)
        self.abb = ABBCollector(self.cfg.abb)
        self.f2pool = F2PoolClient(self.cfg.f2pool)
        self.asics = ASICFleet(self.cfg.asic) if self.cfg.asic.hosts else None
        if self.cfg.ble.enabled:
            self.ble_monitor = BLEMonitor(self.cfg.ble.devices, self.cfg.ble.scan_interval)
        self.llm = LLMBridge(self.cfg.llm, self.db, log_path) if self.cfg.llm.enabled else None
        self.automation = AutomationEngine(self.cfg.automation, self.inverter, self.asics)
        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        tasks = [
            asyncio.create_task(self._inverter_loop(), name="inverter"),
            asyncio.create_task(self._abb_loop(), name="abb"),
            asyncio.create_task(self._f2pool_loop(), name="f2pool"),
            asyncio.create_task(self._automation_loop(), name="automation"),
        ]
        if self.ble_monitor:
            tasks.append(asyncio.create_task(self._ble_loop(), name="ble"))
        if self.asics:
            tasks.append(asyncio.create_task(self._asic_loop(), name="asics"))
        if self.llm:
            tasks.append(asyncio.create_task(self._llm_loop(), name="llm"))
        _LOGGER.info("CentralOS event loops started")
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            _LOGGER.info("CentralOS cancellation requested")
        except Exception:
            _LOGGER.exception("CentralOS encountered an error")
        finally:
            self._stop_event.set()
            for task in tasks:
                task.cancel()

    async def stop(self) -> None:
        self._stop_event.set()

    async def _inverter_loop(self) -> None:
        while not self._stop_event.is_set():
            metrics = await asyncio.to_thread(self.inverter.read_status)
            self.latest_inverter = metrics
            self.db.insert_inverter_metrics(metrics)
            _LOGGER.debug("Inverter metrics: %s", metrics)
            await asyncio.sleep(5)

    async def _abb_loop(self) -> None:
        while not self._stop_event.is_set():
            metrics = await asyncio.to_thread(self.abb.read_metrics)
            self.db.insert_abb_metrics(metrics)
            _LOGGER.debug("ABB metrics: %s", metrics)
            await asyncio.sleep(10)

    async def _f2pool_loop(self) -> None:
        while not self._stop_event.is_set():
            dashboard = await asyncio.to_thread(self.f2pool.fetch_dashboard)
            if dashboard:
                workers = dashboard.get("workers") or 0
                self.latest_workers = int(workers)
                _LOGGER.info(
                    "F2Pool hashrate=%s TH/s 24h=%s TH/s workers=%s",
                    dashboard.get("hashrate"),
                    dashboard.get("hashrate_24h"),
                    workers,
                )
            await asyncio.sleep(self.cfg.f2pool.refresh_interval)

    async def _automation_loop(self) -> None:
        while not self._stop_event.is_set():
            context = AutomationContext(
                inverter=self.latest_inverter,
                sensors=self.latest_sensors,
                asic_online=self.latest_workers,
            )
            await self.automation.apply(context)
            await asyncio.sleep(self.cfg.automation.schedule_interval)

    async def _ble_loop(self) -> None:
        assert self.ble_monitor is not None
        while not self._stop_event.is_set():
            readings = await self.ble_monitor.scan()
            if readings:
                self.latest_sensors = readings
                self.db.insert_sensor_metrics(
                    [
                        {
                            "device": reading.device,
                            "temperature": reading.temperature,
                            "humidity": reading.humidity,
                            "dew_point": reading.dew_point,
                        }
                        for reading in readings
                    ]
                )
            await asyncio.sleep(self.cfg.ble.scan_interval)

    async def _asic_loop(self) -> None:
        assert self.asics is not None
        while not self._stop_event.is_set():
            await self.asics.refresh()
            await asyncio.sleep(60)

    async def _llm_loop(self) -> None:
        assert self.llm is not None
        while not self._stop_event.is_set():
            response = await self.llm.send_log_digest()
            if response:
                _LOGGER.info("LLM summary: %s", response)
            await asyncio.sleep(300)
