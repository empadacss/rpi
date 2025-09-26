"""Bridge between logs and an LLM provider."""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import LLMConfig
from .database import Database

_LOGGER = logging.getLogger(__name__)


@dataclass
class LLMBridge:
    cfg: LLMConfig
    db: Database
    log_path: Path

    def available(self) -> bool:
        if not self.cfg.enabled:
            return False
        if self.cfg.provider != "openai":
            _LOGGER.warning("LLM provider %s not supported", self.cfg.provider)
            return False
        if not os.getenv("OPENAI_API_KEY"):
            _LOGGER.warning("OPENAI_API_KEY not configured; LLM bridge disabled")
            return False
        try:
            import openai  # type: ignore  # noqa
        except Exception as exc:  # pragma: no cover - optional dependency
            _LOGGER.warning("OpenAI library not available: %s", exc)
            return False
        return True

    async def send_log_digest(self, lines: int = 200) -> Optional[str]:
        if not self.available():
            return None
        text = self._tail(lines)
        if not text:
            return None
        return await asyncio.to_thread(self._call_openai, text)

    def _tail(self, lines: int) -> str:
        if not self.log_path.exists():
            return ""
        content = self.log_path.read_text().splitlines()[-lines:]
        return "\n".join(content)

    def _call_openai(self, prompt: str) -> Optional[str]:
        try:
            from openai import OpenAI  # type: ignore
        except Exception:  # pragma: no cover - optional dependency
            _LOGGER.exception("Failed to import OpenAI client")
            return None
        client = OpenAI()
        response = client.chat.completions.create(
            model=self.cfg.model,
            max_tokens=self.cfg.max_tokens,
            temperature=self.cfg.temperature,
            messages=[
                {"role": "system", "content": "You are the monitoring assistant for a mining farm."},
                {"role": "user", "content": prompt},
            ],
        )
        message = response.choices[0].message.content  # type: ignore[index]
        if message:
            self.db.insert_llm_message("assistant", message)
        return message
