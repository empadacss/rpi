"""ASIC fleet management."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List

import aiohttp

from .config import ASICConfig

_LOGGER = logging.getLogger(__name__)


@dataclass
class ASICFleet:
    cfg: ASICConfig
    status: Dict[str, Dict[str, str]] = field(default_factory=dict)

    async def _fetch_json(self, session: aiohttp.ClientSession, host: str, path: str) -> Dict[str, str]:
        url = f"http://{host}/{path}"
        try:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                return await response.json()
        except Exception:
            _LOGGER.exception("Failed to fetch %s", url)
            return {}

    async def refresh(self) -> None:
        if not self.cfg.hosts:
            return
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_json(session, host, "status") for host in self.cfg.hosts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        for host, result in zip(self.cfg.hosts, results):
            if isinstance(result, Exception):
                _LOGGER.error("ASIC %s query failed: %s", host, result)
                continue
            self.status[host] = result
            _LOGGER.debug("ASIC %s status updated", host)

    async def send_command(self, command: str) -> Dict[str, bool]:
        if not self.cfg.hosts:
            return {}
        async with aiohttp.ClientSession() as session:
            tasks = []
            for host in self.cfg.hosts:
                url = f"http://{host}/command/{command}"
                tasks.append(self._command(session, url))
            results = await asyncio.gather(*tasks, return_exceptions=True)
        summary: Dict[str, bool] = {}
        for host, result in zip(self.cfg.hosts, results):
            summary[host] = not isinstance(result, Exception) and result
        return summary

    async def _command(self, session: aiohttp.ClientSession, url: str) -> bool:
        try:
            async with session.post(url, timeout=10) as response:
                response.raise_for_status()
                return True
        except Exception:
            _LOGGER.exception("Failed to send command to %s", url)
            return False

    def summary(self) -> List[Dict[str, str]]:
        return [
            {
                "host": host,
                **status,
            }
            for host, status in self.status.items()
        ]
