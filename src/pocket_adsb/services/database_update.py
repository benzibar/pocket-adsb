from __future__ import annotations

import os
import shutil
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pocket_adsb.services.aircraft_database import AircraftDatabase
from pocket_adsb.services.airline_database import AirlineDatabase


AIRCRAFT_DB_URL = (
    "https://github.com/wiedehopf/tar1090-db/"
    "raw/refs/heads/csv/aircraft.csv.gz"
)

AIRLINE_DB_URL = (
    "https://raw.githubusercontent.com/"
    "jpatokal/openflights/master/data/airlines.dat"
)


@dataclass
class DatabaseUpdateResult:
    aircraft_updated: bool
    airline_updated: bool
    messages: list[str]
    aircraft_record_count: int | None = None
    airline_record_count: int | None = None


class AircraftDatabaseUpdater:
    def __init__(
        self,
        data_dir: str | Path,
        max_age_days: int = 7,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.max_age = timedelta(days=max_age_days)

        self.aircraft_csv_path = (
            self.data_dir / "aircraft.csv.gz"
        )

        self.airline_data_path = (
            self.data_dir / "airlines.dat"
        )

        self.db_path = (
            self.data_dir / "pocket_adsb.db"
        )

    def ensure_database(
        self,
    ) -> DatabaseUpdateResult:
        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        messages: list[str] = []

        aircraft_updated = False
        airline_updated = False

        aircraft_record_count = None
        airline_record_count = None

        # ---------------------------------------
        # Aircraft database
        # ---------------------------------------

        try:
            (
                aircraft_updated,
                aircraft_record_count,
                aircraft_message,
            ) = self._ensure_aircraft_database()

            messages.append(
                aircraft_message
            )

        except Exception as exc:
            messages.append(
                "Aircraft database update failed: "
                f"{exc}"
            )

        # ---------------------------------------
        # Airline database
        # ---------------------------------------

        try:
            (
                airline_updated,
                airline_record_count,
                airline_message,
            ) = self._ensure_airline_database()

            messages.append(
                airline_message
            )

        except Exception as exc:
            messages.append(
                "Airline database update failed: "
                f"{exc}"
            )

        return DatabaseUpdateResult(
            aircraft_updated=aircraft_updated,
            airline_updated=airline_updated,
            messages=messages,
            aircraft_record_count=aircraft_record_count,
            airline_record_count=airline_record_count,
        )

    def _ensure_aircraft_database(
        self,
    ) -> tuple[bool, int | None, str]:
        if not self.db_path.exists():
            return self._bootstrap_aircraft()

        if not self.aircraft_csv_path.exists():
            return self._bootstrap_aircraft()

        if self._file_is_stale(
            self.aircraft_csv_path
        ):
            try:
                return self._refresh_aircraft()

            except Exception as exc:
                return (
                    False,
                    None,
                    "Aircraft refresh failed; "
                    f"using existing data: {exc}",
                )

        return (
            False,
            None,
            "Aircraft database is current",
        )

    def _bootstrap_aircraft(
        self,
    ) -> tuple[bool, int, str]:
        if not self.aircraft_csv_path.exists():
            self._download(
                AIRCRAFT_DB_URL,
                self.aircraft_csv_path,
            )

        database = AircraftDatabase(
            self.db_path
        )

        record_count = (
            database.import_csv_gz(
                self.aircraft_csv_path
            )
        )

        if record_count < 100_000:
            raise RuntimeError(
                "Aircraft database contains "
                "too few records"
            )

        return (
            True,
            record_count,
            "Aircraft database created",
        )

    def _refresh_aircraft(
        self,
    ) -> tuple[bool, int, str]:
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
                self.aircraft_csv_path,
            )

            # Important:
            # We cannot blindly replace the whole DB here,
            # because pocket_adsb.db also contains airlines
            # and route cache tables.
            #
            # So instead, re-import the validated CSV into
            # the live database.
            live_database = AircraftDatabase(
                self.db_path
            )

            live_database.import_csv_gz(
                self.aircraft_csv_path
            )

        return (
            True,
            record_count,
            "Aircraft database updated",
        )

    def _ensure_airline_database(
        self,
    ) -> tuple[bool, int | None, str]:
        airline_database = AirlineDatabase(
            self.db_path
        )

        airline_count = (
            self._count_airlines()
        )

        if (
            not self.airline_data_path.exists()
            or airline_count == 0
        ):
            return self._bootstrap_airlines()

        if self._file_is_stale(
            self.airline_data_path
        ):
            try:
                return self._refresh_airlines()

            except Exception as exc:
                return (
                    False,
                    airline_count,
                    "Airline refresh failed; "
                    f"using existing data: {exc}",
                )

        return (
            False,
            airline_count,
            "Airline database is current",
        )

    def _bootstrap_airlines(
        self,
    ) -> tuple[bool, int, str]:
        if not self.airline_data_path.exists():
            self._download(
                AIRLINE_DB_URL,
                self.airline_data_path,
            )

        database = AirlineDatabase(
            self.db_path
        )

        record_count = (
            database.import_openflights(
                self.airline_data_path
            )
        )

        if record_count < 500:
            raise RuntimeError(
                "Airline database contains "
                "too few records"
            )

        return (
            True,
            record_count,
            "Airline database created",
        )

    def _refresh_airlines(
        self,
    ) -> tuple[bool, int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)

            temp_data = (
                temp_dir / "airlines.dat"
            )

            self._download(
                AIRLINE_DB_URL,
                temp_data,
            )

            temp_db = (
                temp_dir / "airlines.db"
            )

            temp_database = AirlineDatabase(
                temp_db
            )

            record_count = (
                temp_database.import_openflights(
                    temp_data
                )
            )

            if record_count < 500:
                raise RuntimeError(
                    "Downloaded airline database "
                    "contains too few records"
                )

            shutil.copy2(
                temp_data,
                self.airline_data_path,
            )

            live_database = AirlineDatabase(
                self.db_path
            )

            live_database.import_openflights(
                self.airline_data_path
            )

        return (
            True,
            record_count,
            "Airline database updated",
        )

    def _count_airlines(
        self,
    ) -> int:
        if not self.db_path.exists():
            return 0

        import sqlite3

        try:
            with sqlite3.connect(
                self.db_path
            ) as connection:
                row = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM airlines
                    """
                ).fetchone()

            if row is None:
                return 0

            return int(row[0])

        except sqlite3.OperationalError:
            return 0

    def _file_is_stale(
        self,
        path: Path,
    ) -> bool:
        if not path.exists():
            return True

        modified = datetime.fromtimestamp(
            path.stat().st_mtime,
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