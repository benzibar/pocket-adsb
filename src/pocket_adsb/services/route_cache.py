import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class Route:
    flight_id: str
    origin: str
    destination: str
    checked_at: datetime
    source: str


ROUTE_SCHEMA = """
CREATE TABLE IF NOT EXISTS routes (
    flight_id TEXT PRIMARY KEY,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    source TEXT NOT NULL,
    found INTEGER NOT NULL DEFAULT 1
);
"""


class RouteCache:
    def __init__(
        self,
        db_path: str | Path,
        max_age_hours: int = 24,
        negative_max_age_minutes: int = 30,
    ) -> None:
        self.db_path = Path(db_path)
        self.max_age = timedelta(hours=max_age_hours)
        self.negative_max_age = timedelta(
            minutes=negative_max_age_minutes
        )

    def initialise(self) -> None:
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with sqlite3.connect(self.db_path) as connection:
            connection.executescript(ROUTE_SCHEMA)

            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(routes)"
                )
            }

            if "found" not in columns:
                connection.execute(
                    """
                    ALTER TABLE routes
                    ADD COLUMN found INTEGER NOT NULL DEFAULT 1
                    """
                )

            connection.commit()

    def lookup(
        self,
        flight_id: str,
    ) -> Route | None:
        row = self._lookup_row(flight_id)

        if row is None:
            return None

        if not bool(row["found"]):
            return None

        checked_at = datetime.fromisoformat(
            row["checked_at"]
        )

        if (
            datetime.now(timezone.utc) - checked_at
            > self.max_age
        ):
            return None

        return Route(
            flight_id=row["flight_id"],
            origin=row["origin"],
            destination=row["destination"],
            checked_at=checked_at,
            source=row["source"],
        )

    def has_recent_negative(
        self,
        flight_id: str,
    ) -> bool:
        row = self._lookup_row(flight_id)

        if row is None:
            return False

        if bool(row["found"]):
            return False

        checked_at = datetime.fromisoformat(
            row["checked_at"]
        )

        return (
            datetime.now(timezone.utc) - checked_at
            <= self.negative_max_age
        )

    def store(
        self,
        flight_id: str,
        origin: str,
        destination: str,
        source: str,
    ) -> None:
        self._store(
            flight_id=flight_id,
            origin=origin.upper(),
            destination=destination.upper(),
            source=source,
            found=True,
        )

    def store_negative(
        self,
        flight_id: str,
        source: str,
    ) -> None:
        self._store(
            flight_id=flight_id,
            origin="",
            destination="",
            source=source,
            found=False,
        )

    def _store(
        self,
        flight_id: str,
        origin: str,
        destination: str,
        source: str,
        found: bool,
    ) -> None:
        normalised = self.normalise_flight_id(
            flight_id
        )

        if not normalised:
            return

        self.initialise()

        checked_at = datetime.now(
            timezone.utc
        ).isoformat()

        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO routes (
                    flight_id,
                    origin,
                    destination,
                    checked_at,
                    source,
                    found
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(flight_id)
                DO UPDATE SET
                    origin = excluded.origin,
                    destination = excluded.destination,
                    checked_at = excluded.checked_at,
                    source = excluded.source,
                    found = excluded.found
                """,
                (
                    normalised,
                    origin,
                    destination,
                    checked_at,
                    source,
                    int(found),
                ),
            )

            connection.commit()

    def _lookup_row(
        self,
        flight_id: str,
    ) -> sqlite3.Row | None:
        if not self.db_path.exists():
            return None

        normalised = self.normalise_flight_id(
            flight_id
        )

        if not normalised:
            return None

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            return connection.execute(
                """
                SELECT
                    flight_id,
                    origin,
                    destination,
                    checked_at,
                    source,
                    found
                FROM routes
                WHERE flight_id = ?
                """,
                (normalised,),
            ).fetchone()

    @staticmethod
    def normalise_flight_id(
        flight_id: str,
    ) -> str:
        return flight_id.strip().upper()