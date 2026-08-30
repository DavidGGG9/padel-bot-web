import asyncio
import logging
import sys

from src.configs.settings import settings
from src.export.exporter import Exporter

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    exporter = Exporter(settings)
    await exporter.export_availabilities()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as err:
        print(f"Export failed: {err}", file=sys.stderr)
        sys.exit(1)
