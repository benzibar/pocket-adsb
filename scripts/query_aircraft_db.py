import sqlite3


def main() -> None:
    connection = sqlite3.connect(
        "data/pocket_adsb.db"
    )

    try:
        rows = connection.execute(
            """
            SELECT
                icao,
                registration,
                aircraft_type,
                operator
            FROM aircraft
            WHERE icao LIKE ?
              AND registration != ?
            LIMIT 10
            """,
            ("4CA%", ""),
        ).fetchall()

        for row in rows:
            print(row)

    finally:
        connection.close()


if __name__ == "__main__":
    main()