"""Command-line interface for CentralOS."""
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from .config import load_config
from .service import CentralOS


async def _run_service(config_path: Path) -> None:
    cfg = load_config(config_path)
    service = CentralOS(cfg)
    await service.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="CentralOS unified control system")
    parser.add_argument("--config", type=Path, default=Path("centralos.yaml"), help="Path to configuration file")
    args = parser.parse_args()

    try:
        asyncio.run(_run_service(args.config))
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("CentralOS stopped by user")


if __name__ == "__main__":
    main()
