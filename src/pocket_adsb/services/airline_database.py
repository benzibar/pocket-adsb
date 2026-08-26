import csv
import sqlite3
from pathlib import Path


AIRLINE_SCHEMA = """
CREATE TABLE IF NOT EXISTS airlines (
    icao TEXT PRIMARY KEY,
    iata TEXT,
    name TEXT,
    callsign TEXT,
    country TEXT,
    active INTEGER NOT NULL DEFAULT 0
);
"""


class AirlineDatabase:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def initialise(self) -> None:
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with sqlite3.connect(self.db_path) as connection:
            connection.executescript(AIRLINE_SCHEMA)

    def lookup(self, icao: str) -> dict[str, str] | None:
        if not self.db_path.exists():
            return None

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            row = connection.execute(
                """
                SELECT
                    icao,
                    iata,
                    name,
                    callsign,
                    country,
                    active
                FROM airlines
                WHERE icao = ?
                """,
                (icao.upper(),),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def import_openflights(
        self,
        source_path: str | Path,
    ) -> int:
        source_path = Path(source_path)

        self.initialise()

        rows: list[tuple[str, str, str, str, str, int]] = []

        with source_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            reader = csv.reader(file)

            for raw in reader:
                if len(raw) < 8:
                    continue

                name = self._clean(raw[1])
                iata = self._clean(raw[3])
                icao = self._clean(raw[4]).upper()
                callsign = self._clean(raw[5])
                country = self._clean(raw[6])
                active = 1 if raw[7].strip() == "Y" else 0

                if not icao or len(icao) != 3:
                    continue

                rows.append(
                    (
                        icao,
                        iata,
                        name,
                        callsign,
                        country,
                        active,
                    )
                )

        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "DELETE FROM airlines"
            )

            connection.executemany(
                """
                INSERT OR REPLACE INTO airlines (
                    icao,
                    iata,
                    name,
                    callsign,
                    country,
                    active
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

            connection.commit()

        return len(rows)

    @staticmethod
    def _clean(value: str) -> str:
        value = value.strip()

        if value == r"\N":
            return ""

        return value