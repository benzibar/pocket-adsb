import csv
import gzip
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS aircraft (
    icao TEXT PRIMARY KEY,
    registration TEXT,
    aircraft_type TEXT,
    flags TEXT,
    description TEXT,
    year TEXT,
    operator TEXT
);

CREATE INDEX IF NOT EXISTS idx_aircraft_registration
ON aircraft(registration);
"""


class AircraftDatabase:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def initialise(self) -> None:
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with sqlite3.connect(self.db_path) as connection:
            connection.executescript(SCHEMA)

    def lookup(self, icao: str) -> dict[str, str] | None:
        if not self.db_path.exists():
            return None

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            row = connection.execute(
                """
                SELECT
                    icao,
                    registration,
                    aircraft_type,
                    flags,
                    description,
                    year,
                    operator
                FROM aircraft
                WHERE icao = ?
                """,
                (icao.upper(),),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def import_csv_gz(
        self,
        csv_gz_path: str | Path,
    ) -> int:
        csv_gz_path = Path(csv_gz_path)

        if not csv_gz_path.exists():
            raise FileNotFoundError(
                f"Aircraft database not found: {csv_gz_path}"
            )

        self.initialise()

        rows: list[
            tuple[
                str,
                str,
                str,
                str,
                str,
                str,
                str,
            ]
        ] = []

        with gzip.open(
            csv_gz_path,
            "rt",
            encoding="utf-8",
            newline="",
        ) as file:
            reader = csv.reader(
                file,
                delimiter=";",
                escapechar="\\",
                quoting=csv.QUOTE_NONE,
            )

            for raw in reader:
                if not raw:
                    continue

                if len(raw) < 7:
                    continue

                icao = raw[0].strip().upper()

                if not icao:
                    continue

                registration = raw[1].strip()
                aircraft_type = raw[2].strip()
                flags = raw[3].strip()
                description = raw[4].strip()
                year = raw[5].strip()
                operator = raw[6].strip()

                rows.append(
                    (
                        icao,
                        registration,
                        aircraft_type,
                        flags,
                        description,
                        year,
                        operator,
                    )
                )

        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "DELETE FROM aircraft"
            )

            connection.executemany(
                """
                INSERT OR REPLACE INTO aircraft (
                    icao,
                    registration,
                    aircraft_type,
                    flags,
                    description,
                    year,
                    operator
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

            connection.commit()

        return len(rows)