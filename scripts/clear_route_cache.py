import sqlite3


def main() -> None:
    connection = sqlite3.connect(
        "data/pocket_adsb.db"
    )

    try:
        connection.execute(
            "DELETE FROM routes"
        )
        connection.commit()

        print("Route cache cleared")

    finally:
        connection.close()


if __name__ == "__main__":
    main()