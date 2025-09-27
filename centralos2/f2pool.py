"""Client for the F2Pool API."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

import requests

from .config import F2PoolConfig

_LOGGER = logging.getLogger(__name__)


@dataclass
class F2PoolClient:
    cfg: F2PoolConfig
    session: requests.Session = field(default_factory=requests.Session)

    API_BASE = "https://api.f2pool.com"

    def _endpoint(self, path: str) -> str:
        return f"{self.API_BASE}/{self.cfg.coin}/{self.cfg.user}/{path}" if path else f"{self.API_BASE}/{self.cfg.coin}/{self.cfg.user}"

    def fetch_dashboard(self) -> Optional[Dict[str, float]]:
        try:
            response = self.session.get(self._endpoint(""), timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                "hashrate": data.get("hashrate"),
                "hashrate_24h": data.get("hashrate_last_24h"),
                "workers": data.get("worker_length"),
            }
        except Exception:
            _LOGGER.exception("Failed to fetch F2Pool dashboard")
            return None

    def fetch_history(self) -> Optional[Dict[str, float]]:
        try:
            response = self.session.get(self._endpoint("workers"), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception:
            _LOGGER.exception("Failed to fetch F2Pool history")
            return None
