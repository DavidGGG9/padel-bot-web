import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.configs.mongo_client import instantiate_mongodb_client
from src.configs.settings import Settings

logger = logging.getLogger(__name__)


class Exporter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @staticmethod
    def _map_availabilities(doc: dict) -> dict:
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

    @staticmethod
    def _map_scrape_run(doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "club": doc["club"],
            "availabilityDate": doc["availability_date"],
            "scrapedAt": doc["scraped_at"].isoformat(),
            "slotsCount": doc["slots_count"],
            "status": doc["status"],
        }

    @staticmethod
    def _map_meteo_run(doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "club": doc["club"],
            "modelDatetime": doc["model_datetime"],
            "localDatetime": doc["local_datetime"],
            "precipMm1h": float(doc["precip_mm_1h"]),
            "ghiWm2": float(doc["ghi_w_m2"]),
            "clearskyWm2": float(doc["clearsky_w_m2"]),
            "sunRatio": None if doc["sun_ratio"] is None else float(doc["sun_ratio"]),
            "flag": doc["flag"],
        }

    async def export_availabilities(self) -> None:
        tz = ZoneInfo(self._settings.TIMEZONE)
        now = datetime.now(tz=tz)
        today = now.date().isoformat()

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

            availabilities = [self._map_availabilities(doc) for doc in latest.values()]

            # Keep only slots whose end time is at least 30 minutes from now.
            cutoff = now + timedelta(minutes=30)
            availabilities = [
                slot
                for slot in availabilities
                if (
                    datetime.fromisoformat(slot["start"]).replace(tzinfo=tz)
                    + timedelta(minutes=slot["durationMinutes"])
                ) >= cutoff
            ]

            output = {
                "generatedAt": datetime.now(UTC).isoformat(),
                "availabilities": availabilities,
            }

            output_path = Path(self._settings.AVAILABILITIES_OUTPUT_PATH).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

            logger.info("Wrote %d availabilities to %s", len(availabilities), output_path)

    async def export_scrape_runs(self) -> None:
        tz = ZoneInfo(self._settings.TIMEZONE)
        now = datetime.now(tz=tz)
        today = now.date().isoformat()
        
        async with instantiate_mongodb_client(
            user=self._settings.MDB_USER,
            password=self._settings.MDB_PASSWORD.get_secret_value(),
        ) as client:
            collection = client[self._settings.DB_NAME]["scrape_runs"]

            cursor = collection\
                .find({"availability_date": {"$gte": today}})\
                .sort([("availability_date", 1), ("club", 1), ("scraped_at", -1)])
            raw_docs = await cursor.to_list(length=None)

            # Dedup: keep only the most recent scraped_at per (club, availability_date).
            latest: dict[tuple, dict] = {}
            for doc in raw_docs:
                key = (doc["club"], doc["availability_date"])
                if key not in latest or doc["scraped_at"] > latest[key]["scraped_at"]:
                    latest[key] = doc

            scrape_runs = [self._map_scrape_run(doc) for doc in latest.values()]
            scrape_runs.sort(key=lambda item: (item["availabilityDate"], item["club"]))

            output = {
                "generatedAt": datetime.now(UTC).isoformat(),
                "scrapeRuns": scrape_runs,
            }

            output_path = Path(self._settings.SCRAPE_RUNS_OUTPUT_PATH).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

            logger.info("Wrote %d scrape runs to %s", len(scrape_runs), output_path)


    async def export_meteo_runs(self) -> None:
        async with instantiate_mongodb_client(
            user=self._settings.MDB_USER,
            password=self._settings.MDB_PASSWORD.get_secret_value(),
        ) as client:
            collection = client[self._settings.DB_NAME]["meteo_runs"]

            raw_docs = await collection.find({}).to_list(length=None)

            # Dedup: keep only the most recent model_datetime per club.
            # Keeping every forecast row (local_datetime) of that latest run.
            latest_model: dict[str, str] = {}
            for doc in raw_docs:
                club = doc["club"]
                if club not in latest_model or doc["model_datetime"] > latest_model[club]:
                    latest_model[club] = doc["model_datetime"]

            meteo_runs = [
                self._map_meteo_run(doc)
                for doc in raw_docs
                if doc["model_datetime"] == latest_model[doc["club"]]
            ]
            meteo_runs.sort(key=lambda item: (item["club"], item["localDatetime"]))

            output = {
                "generatedAt": datetime.now(UTC).isoformat(),
                "meteoRuns": meteo_runs,
            }

            output_path = Path(self._settings.METEO_RUNS_OUTPUT_PATH).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # write_text overwrites any existing file on every export
            output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

            logger.info("Wrote %d meteo runs to %s", len(meteo_runs), output_path)
