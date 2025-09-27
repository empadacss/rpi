"""Compatibility launcher for the modular CentralOS2 package."""
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from centralos2 import CentralOS, load_config


async def _run(config_path: Path) -> None:
    cfg = load_config(config_path)
    service = CentralOS(cfg)
    await service.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CentralOS2 control service")
    parser.add_argument("--config", type=Path, default=Path("centralos.yaml"), help="Path to the configuration file")
    args = parser.parse_args()

    try:
        asyncio.run(_run(args.config))
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("CentralOS interrupted by user")


if __name__ == "__main__":
    main()
