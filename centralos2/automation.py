"""Automation engine."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional

from .asic import ASICFleet
from .ble import BLESensorReading
from .config import AutomationConfig, AutomationRule
from .modbus import InverterController

_LOGGER = logging.getLogger(__name__)


@dataclass
class AutomationContext:
    inverter: dict
    sensors: List[BLESensorReading]
    asic_online: int = 0


class AutomationEngine:
    def __init__(self, cfg: AutomationConfig, inverter: InverterController, asics: Optional[ASICFleet] = None):
        self.cfg = cfg
        self.inverter = inverter
        self.asics = asics

    async def apply(self, context: AutomationContext) -> None:
        tasks = []
        for rule in self.cfg.rules:
            if not rule.enabled:
                continue
            handler = getattr(self, f"_rule_{rule.name}", None)
            if handler:
                tasks.append(handler(context, rule))
            else:
                _LOGGER.debug("No handler for rule %s", rule.name)
        if tasks:
            await asyncio.gather(*tasks)

    async def _rule_inverter_safety(self, context: AutomationContext, rule: AutomationRule) -> None:
        state = context.inverter.get("state")
        if state in (None, 1):
            return
        if context.asic_online <= 0:
            return
        command = rule.parameters.get("command", "sleep")
        if self.asics:
            result = await self.asics.send_command(command)
            _LOGGER.warning("Inverter not running; sent %s to ASICs: %s", command, result)

    async def _rule_humidity_guard(self, context: AutomationContext, rule: AutomationRule) -> None:
        if not context.sensors:
            return
        threshold = rule.parameters.get("threshold", 90)
        forced_speed = rule.parameters.get("speed", 20)
        humidity = max((sensor.humidity or 0.0) for sensor in context.sensors)
        if humidity >= threshold:
            _LOGGER.warning("Humidity %.2f >= %s%%, forcing inverter speed to %s", humidity, threshold, forced_speed)
            self.inverter.set_speed(int(forced_speed))

    async def _rule_dew_point_guard(self, context: AutomationContext, rule: AutomationRule) -> None:
        if not context.sensors:
            return
        diff_threshold = rule.parameters.get("diff", 4.0)
        forced_speed = rule.parameters.get("speed", 10)
        for sensor in context.sensors:
            if sensor.temperature is None or sensor.dew_point is None:
                continue
            diff = sensor.temperature - sensor.dew_point
            if diff < diff_threshold:
                _LOGGER.warning(
                    "Dew point diff %.2f < %.2f for %s; forcing speed %s",
                    diff,
                    diff_threshold,
                    sensor.device,
                    forced_speed,
                )
                self.inverter.set_speed(int(forced_speed))
                break
