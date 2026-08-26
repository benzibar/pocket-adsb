from __future__ import annotations

import os
import shutil
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pocket_adsb.services.aircraft_database import AircraftDatabase


AIRCRAFT_DB_URL = (
    "https://github.com/wiedehopf/tar1090-db/"
    "raw/refs/heads/csv/aircraft.csv.gz"
)


@dataclass
class DatabaseUpdateResult:
    updated: bool
    message: str
    record_count: int | None = None


class AircraftDatabaseUpdater:
    def __init__(
        self,
        data_dir: str | Path,
        max_age_days: int = 7,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.max_age = timedelta(days=max_age_days)

        self.csv_path = self.data_dir / "aircraft.csv.gz"
        self.db_path = self.data_dir / "pocket_adsb.db"

    def ensure_database(self) -> DatabaseUpdateResult:
        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.db_path.exists():
            return self._bootstrap()

        if self._database_is_stale():
            try:
                return self._refresh()
            except Exception as exc:
                return DatabaseUpdateResult(
                    updated=False,
                    message=(
                        "Database refresh failed; "
                        f"using existing database: {exc}"
                    ),
                )

        return DatabaseUpdateResult(
            updated=False,
            message="Aircraft database is current",
        )

    def _bootstrap(self) -> DatabaseUpdateResult:
        if not self.csv_path.exists():
            self._download(
                AIRCRAFT_DB_URL,
                self.csv_path,
            )

        database = AircraftDatabase(
            self.db_path
        )

        record_count = database.import_csv_gz(
            self.csv_path
        )

        return DatabaseUpdateResult(
            updated=True,
            message="Aircraft database created",
            record_count=record_count,
        )

    def _refresh(self) -> DatabaseUpdateResult:
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)

            temp_csv = (
                temp_dir / "aircraft.csv.gz"
            )

            temp_db = (
                temp_dir / "pocket_adsb.db"
            )

            self._download(
                AIRCRAFT_DB_URL,
                temp_csv,
            )

            temp_database = AircraftDatabase(
                temp_db
            )

            record_count = (
                temp_database.import_csv_gz(
                    temp_csv
                )
            )

            if record_count < 100_000:
                raise RuntimeError(
                    "Downloaded aircraft database "
                    "contains too few records"
                )

            shutil.copy2(
                temp_csv,
                self.csv_path,
            )

            os.replace(
                temp_db,
                self.db_path,
            )

        return DatabaseUpdateResult(
            updated=True,
            message="Aircraft database updated",
            record_count=record_count,
        )

    def _database_is_stale(self) -> bool:
        modified = datetime.fromtimestamp(
            self.db_path.stat().st_mtime,
            tz=timezone.utc,
        )

        age = (
            datetime.now(timezone.utc)
            - modified
        )

        return age > self.max_age

    @staticmethod
    def _download(
        url: str,
        destination: Path,
    ) -> None:
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Pocket-ADS-B/0.1"
                )
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:
            with destination.open(
                "wb"
            ) as file:
                shutil.copyfileobj(
                    response,
                    file,
                )