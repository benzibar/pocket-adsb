import argparse
from pathlib import Path

from pocket_adsb.services.aircraft_database import AircraftDatabase


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import aircraft metadata into Pocket ADS-B SQLite database.",
    )

    parser.add_argument(
        "source",
        type=Path,
        help="Path to aircraft.csv.gz",
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/pocket_adsb.db"),
        help="SQLite database path",
    )

    args = parser.parse_args()

    database = AircraftDatabase(args.db)

    count = database.import_csv_gz(args.source)

    print(f"Imported {count:,} aircraft")
    print(f"Database: {args.db}")


if __name__ == "__main__":
    main()