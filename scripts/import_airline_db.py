from pathlib import Path

from pocket_adsb.services.airline_database import AirlineDatabase


def main() -> None:
    source = Path("data/airlines.dat")
    database_path = Path("data/pocket_adsb.db")

    database = AirlineDatabase(
        database_path
    )

    count = database.import_openflights(
        source
    )

    print(f"Imported {count:,} airlines")
    print(f"Database: {database_path}")


if __name__ == "__main__":
    main()