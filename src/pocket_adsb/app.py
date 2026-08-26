import argparse
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Footer, Header, Static

from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.services.adsbdb_route_provider import (
    AdsbDbRouteProvider,
)
from pocket_adsb.services.adsbim_route_provider import (
    AdsbImRouteProvider,
)
from pocket_adsb.services.aircraft_database import AircraftDatabase
from pocket_adsb.services.airline_database import AirlineDatabase
from pocket_adsb.services.consensus_route_provider import (
    ConsensusRouteProvider,
)
from pocket_adsb.services.data_source import AircraftDataSource
from pocket_adsb.services.database_update import AircraftDatabaseUpdater
from pocket_adsb.services.enrichment import AircraftEnricher
from pocket_adsb.services.network_status import NetworkStatusService
from pocket_adsb.services.position_source import FixedPositionSource
from pocket_adsb.services.readsb import ReadsbDataSource
from pocket_adsb.services.route_cache import RouteCache
from pocket_adsb.services.route_service import RouteService
from pocket_adsb.services.simulator import AircraftSimulator
from pocket_adsb.ui.aircraft_detail import AircraftDetailScreen
from pocket_adsb.ui.radar import RadarScreen
from pocket_adsb.utils.formatting import (
    format_altitude,
    format_direction,
    format_distance,
    format_seen,
    format_speed,
)


class PocketADSB(App):
    TITLE = "Pocket ADS-B"

    BINDINGS = [
        ("x", "open_radar", "Radar"),
        ("d", "sort_distance", "Dist"),
        ("a", "sort_altitude", "Alt"),
        ("c", "sort_callsign", "Call"),
        ("s", "sort_seen", "Seen"),
        ("r", "refresh", "Ref"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        layout: vertical;
    }

    #aircraft-table {
        height: 1fr;
    }

    #receiver-status {
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        data_source: AircraftDataSource,
    ) -> None:
        super().__init__()

        self.data_source = data_source
        self.aircraft: list[Aircraft] = []
        self.selected_aircraft_icao: str | None = None

        self.sort_field = "DIST"
        self.sort_reverse = False

        database_path = Path(
            "data/pocket_adsb.db"
        )

        self.aircraft_database = AircraftDatabase(
            database_path
        )

        self.airline_database = AirlineDatabase(
            database_path
        )

        self.route_cache = RouteCache(
            database_path,
            max_age_hours=2,
            negative_max_age_minutes=30,
        )

        self.route_cache.initialise()

        self.route_provider = ConsensusRouteProvider(
            providers=[
                AdsbDbRouteProvider(),
                AdsbImRouteProvider(),
            ]
        )

        self.route_service = RouteService(
            cache=self.route_cache,
            provider=self.route_provider,
        )

        self.aircraft_enricher = AircraftEnricher(
            aircraft_database=self.aircraft_database,
            airline_database=self.airline_database,
            route_service=self.route_service,
        )

        self.network_status = NetworkStatusService(
            cache_seconds=5.0
        )

    def compose(self) -> ComposeResult:
        yield Header()

        with Container():
            yield DataTable(
                id="aircraft-table"
            )

        yield Static(
            "INITIALISING...",
            id="receiver-status",
        )

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(
            "#aircraft-table",
            DataTable,
        )

        table.cursor_type = "row"
        table.zebra_stripes = True

        table.add_columns(
            "CALL",
            "ALT",
            "SPD",
            "TRK",
            "BRG",
            "DIST",
            "SEEN",
        )

        self.refresh_aircraft()

        self.set_interval(
            1.0,
            self.refresh_aircraft,
        )

    def on_unmount(self) -> None:
        self.route_service.shutdown()

    def get_sorted_aircraft(
        self,
    ) -> list[Aircraft]:
        aircraft = list(
            self.aircraft
        )

        if self.sort_field == "DIST":
            key = lambda item: (
                item.distance_nm is None,
                item.distance_nm or 0,
            )

        elif self.sort_field == "ALT":
            key = lambda item: (
                item.altitude_ft is None,
                item.altitude_ft or 0,
            )

        elif self.sort_field == "CALL":
            key = lambda item: (
                item.callsign
                or item.icao
            )

        elif self.sort_field == "SEEN":
            key = lambda item: (
                item.seen_seconds
            )

        else:
            key = lambda item: (
                item.icao
            )

        return sorted(
            aircraft,
            key=key,
            reverse=self.sort_reverse,
        )

    def get_sort_indicator(
        self,
    ) -> str:
        labels = {
            "DIST": "D",
            "ALT": "A",
            "CALL": "C",
            "SEEN": "S",
        }

        direction = (
            "↓"
            if self.sort_reverse
            else "↑"
        )

        return (
            f"{labels[self.sort_field]}"
            f"{direction}"
        )

    def refresh_aircraft(
        self,
    ) -> None:
        self.aircraft = (
            self.data_source.get_aircraft()
        )

        self.aircraft = (
            self.aircraft_enricher.enrich_all(
                self.aircraft
            )
        )

        receiver_status = (
            self.data_source.get_status()
        )

        wifi_status = (
            self.network_status.status_text()
        )

        sorted_aircraft = (
            self.get_sorted_aircraft()
        )

        table = self.query_one(
            "#aircraft-table",
            DataTable,
        )

        selected_icao = (
            self.selected_aircraft_icao
        )

        selected_row: int | None = None

        table.clear()

        for (
            row_index,
            aircraft,
        ) in enumerate(
            sorted_aircraft
        ):
            table.add_row(
                (
                    aircraft.callsign
                    or aircraft.icao
                ),
                format_altitude(
                    aircraft.altitude_ft
                ),
                format_speed(
                    aircraft.speed_kt
                ),
                format_direction(
                    aircraft.track_deg
                ),
                format_direction(
                    aircraft.bearing_from_us_deg
                ),
                format_distance(
                    aircraft.distance_nm
                ),
                format_seen(
                    aircraft.seen_seconds
                ),
                key=aircraft.icao,
            )

            if (
                aircraft.icao
                == selected_icao
            ):
                selected_row = (
                    row_index
                )

        if selected_row is not None:
            table.move_cursor(
                row=selected_row
            )

        status = self.query_one(
            "#receiver-status",
            Static,
        )

        status.update(
            f"{receiver_status.mode} | "
            f"AC {receiver_status.aircraft_count} | "
            f"{receiver_status.message_rate:.0f}/s | "
            f"GPS {receiver_status.gps_status} | "
            f"WIFI {wifi_status} | "
            f"{self.get_sort_indicator()}"
        )

    def set_sort(
        self,
        field: str,
        default_reverse: bool = False,
    ) -> None:
        if self.sort_field == field:
            self.sort_reverse = (
                not self.sort_reverse
            )
        else:
            self.sort_field = field
            self.sort_reverse = (
                default_reverse
            )

        self.refresh_aircraft()

    def action_open_radar(
        self,
    ) -> None:
        self.push_screen(
            RadarScreen(
                selected_icao=(
                    self.selected_aircraft_icao
                )
            )
        )

    def action_sort_distance(
        self,
    ) -> None:
        self.set_sort(
            "DIST"
        )

    def action_sort_altitude(
        self,
    ) -> None:
        self.set_sort(
            "ALT",
            default_reverse=True,
        )

    def action_sort_callsign(
        self,
    ) -> None:
        self.set_sort(
            "CALL"
        )

    def action_sort_seen(
        self,
    ) -> None:
        self.set_sort(
            "SEEN"
        )

    def action_refresh(
        self,
    ) -> None:
        self.refresh_aircraft()

    def on_data_table_row_highlighted(
        self,
        event: DataTable.RowHighlighted,
    ) -> None:
        if event.row_key.value is not None:
            self.selected_aircraft_icao = str(
                event.row_key.value
            )

    def on_data_table_row_selected(
        self,
        event: DataTable.RowSelected,
    ) -> None:
        aircraft_icao = str(
            event.row_key.value
        )

        aircraft = next(
            (
                item
                for item in self.aircraft
                if item.icao == aircraft_icao
            ),
            None,
        )

        if aircraft is not None:
            self.push_screen(
                AircraftDetailScreen(
                    aircraft
                )
            )


def create_data_source(
    source: str,
    readsb_path: Path,
) -> AircraftDataSource:
    if source == "readsb":
        position_source = FixedPositionSource(
            latitude=52.15,
            longitude=-2.22,
        )

        return ReadsbDataSource(
            readsb_path,
            position_source=position_source,
        )

    return AircraftSimulator()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pocket ADS-B",
    )

    parser.add_argument(
        "--source",
        choices=(
            "sim",
            "readsb",
        ),
        default="sim",
        help="Aircraft data source",
    )

    parser.add_argument(
        "--readsb-path",
        type=Path,
        default=Path(
            "test_data/readsb_aircraft.json"
        ),
        help=(
            "Path to readsb aircraft.json "
            "(default: test_data/readsb_aircraft.json)"
        ),
    )

    args = parser.parse_args()

    updater = AircraftDatabaseUpdater(
        data_dir=Path("data"),
        max_age_days=7,
    )

    result = updater.ensure_database()

    for message in result.messages:
        print(message)

    if result.aircraft_record_count is not None:
        print(
            f"Aircraft records: "
            f"{result.aircraft_record_count:,}"
        )

    if result.airline_record_count is not None:
        print(
            f"Airline records: "
            f"{result.airline_record_count:,}"
        )

    data_source = create_data_source(
        source=args.source,
        readsb_path=args.readsb_path,
    )

    PocketADSB(
        data_source
    ).run()


if __name__ == "__main__":
    main()