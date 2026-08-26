from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Footer, Header, Static

from pocket_adsb.services.data_source import AircraftDataSource
from pocket_adsb.services.simulator import AircraftSimulator
from pocket_adsb.ui.aircraft_detail import AircraftDetailScreen
from pocket_adsb.utils.compass import degrees_to_compass


class PocketADSB(App):
    TITLE = "Pocket ADS-B"
    SUB_TITLE = "Simulated receiver"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
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

    def __init__(self) -> None:
        super().__init__()

        self.data_source: AircraftDataSource = AircraftSimulator()
        self.aircraft = []
        self.selected_aircraft_icao: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Container():
            yield DataTable(id="aircraft-table")

        yield Static(
            "INITIALISING...",
            id="receiver-status",
        )

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#aircraft-table", DataTable)

        table.cursor_type = "row"
        table.zebra_stripes = True

        table.add_columns(
            "CALL",
            "REG",
            "TYPE",
            "ALT",
            "SPD",
            "TRK",
            "BRG",
            "DIST",
            "ROUTE",
            "SEEN",
        )

        self.refresh_aircraft()
        self.set_interval(1.0, self.refresh_aircraft)

    def refresh_aircraft(self) -> None:
        self.aircraft = self.data_source.get_aircraft()
        receiver_status = self.data_source.get_status()

        table = self.query_one("#aircraft-table", DataTable)

        selected_icao = self.selected_aircraft_icao
        selected_row: int | None = None

        table.clear()

        for row_index, aircraft in enumerate(self.aircraft):
            table.add_row(
                aircraft.callsign,
                aircraft.registration,
                aircraft.aircraft_type,
                f"{aircraft.altitude_ft:,}",
                f"{aircraft.speed_kt}",
                degrees_to_compass(aircraft.track_deg),
                degrees_to_compass(aircraft.bearing_from_us_deg),
                f"{aircraft.distance_nm:.1f}",
                f"{aircraft.origin}>{aircraft.destination}",
                f"{aircraft.seen_seconds:.1f}s",
                key=aircraft.icao,
            )

            if aircraft.icao == selected_icao:
                selected_row = row_index

        if selected_row is not None:
            table.move_cursor(row=selected_row)

        status = self.query_one("#receiver-status", Static)

        status.update(
            f"{receiver_status.mode} | "
            f"AIRCRAFT {receiver_status.aircraft_count} | "
            f"MSG {receiver_status.message_rate:.0f}/s | "
            f"GPS {receiver_status.gps_status} | "
            f"WIFI {receiver_status.wifi_status}"
        )

    def on_data_table_row_highlighted(
        self,
        event: DataTable.RowHighlighted,
    ) -> None:
        if event.row_key.value is not None:
            self.selected_aircraft_icao = str(event.row_key.value)

    def on_data_table_row_selected(
        self,
        event: DataTable.RowSelected,
    ) -> None:
        aircraft_icao = str(event.row_key.value)

        aircraft = next(
            (
                item
                for item in self.aircraft
                if item.icao == aircraft_icao
            ),
            None,
        )

        if aircraft is not None:
            self.push_screen(AircraftDetailScreen(aircraft))

    def action_refresh(self) -> None:
        self.refresh_aircraft()


if __name__ == "__main__":
    PocketADSB().run()