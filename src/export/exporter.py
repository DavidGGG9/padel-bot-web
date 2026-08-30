import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.configs.mongo_client import instantiate_mongodb_client
from src.configs.settings import Settings

logger = logging.getLogger(__name__)


class Exporter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @staticmethod
    def _map_document(doc: dict) -> dict:
        availability_date: str = doc["availability_date"]
        availability_time: str = doc["availability_time"]

        # Build a combined ISO datetime string (date + time, no timezone assumed)
        start_iso = f"{availability_date}T{availability_time}"

        return {
            "id": str(doc["_id"]),
            "region": doc["region"],
            "city": doc["city"],
            "club": doc["club"],
            "court": doc["court"],
            "start": start_iso,
            "durationMinutes": doc["availability_duration"],
        }

    async def export_availabilities(self) -> None:
        today = datetime.now(tz=ZoneInfo(self._settings.TIMEZONE)).date().isoformat()

        async with instantiate_mongodb_client(
            user=self._settings.MDB_USER,
            password=self._settings.MDB_PASSWORD.get_secret_value(),
        ) as client:
            collection = client[self._settings.DB_NAME][self._settings.COLLECTION_NAME]

            cursor = (
                collection
                .find({"availability_date": {"$gte": today}})
                .sort([("availability_date", 1), ("availability_time", 1)])
            )

            raw_docs = await cursor.to_list(length=None)

            # Dedup: keep the document with the latest scraping_datetime per
            # (club, court, availability_date, availability_time) combination.
            latest: dict[tuple, dict] = {}
            for doc in raw_docs:
                key = (
                    doc["club"],
                    doc["court"],
                    doc["availability_date"],
                    doc["availability_time"],
                )
                if key not in latest or doc["scraping_datetime"] > latest[key]["scraping_datetime"]:
                    latest[key] = doc

            availabilities = [self._map_document(doc) for doc in latest.values()]

            output = {
                "generatedAt": datetime.now(UTC).isoformat(),
                "availabilities": availabilities,
            }

            output_path = Path(self._settings.OUTPUT_PATH).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

            logger.info("Wrote %d availabilities to %s", len(availabilities), output_path)
