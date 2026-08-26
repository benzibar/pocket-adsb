from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Footer, Header, Static

from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.services.data_source import AircraftDataSource
from pocket_adsb.services.simulator import AircraftSimulator
from pocket_adsb.ui.aircraft_detail import AircraftDetailScreen
from pocket_adsb.utils.compass import degrees_to_compass


class PocketADSB(App):
    TITLE = "Pocket ADS-B"
    SUB_TITLE = "Simulated receiver"

    BINDINGS = [
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

    def __init__(self) -> None:
        super().__init__()

        self.data_source: AircraftDataSource = AircraftSimulator()
        self.aircraft: list[Aircraft] = []
        self.selected_aircraft_icao: str | None = None

        self.sort_field = "DIST"
        self.sort_reverse = False

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
            "ALT",
            "SPD",
            "TRK",
            "BRG",
            "DIST",
            "SEEN",
        )

        self.refresh_aircraft()
        self.set_interval(1.0, self.refresh_aircraft)

    def get_sorted_aircraft(self) -> list[Aircraft]:
        aircraft = list(self.aircraft)

        if self.sort_field == "DIST":
            key = lambda item: item.distance_nm
        elif self.sort_field == "ALT":
            key = lambda item: item.altitude_ft
        elif self.sort_field == "CALL":
            key = lambda item: item.callsign
        elif self.sort_field == "SEEN":
            key = lambda item: item.seen_seconds
        else:
            key = lambda item: item.distance_nm

        return sorted(
            aircraft,
            key=key,
            reverse=self.sort_reverse,
        )

    def get_sort_indicator(self) -> str:
        labels = {
            "DIST": "D",
            "ALT": "A",
            "CALL": "C",
            "SEEN": "S",
        }

        direction = "↓" if self.sort_reverse else "↑"

        return f"{labels[self.sort_field]}{direction}"

    def refresh_aircraft(self) -> None:
        self.aircraft = self.data_source.get_aircraft()
        receiver_status = self.data_source.get_status()

        sorted_aircraft = self.get_sorted_aircraft()

        table = self.query_one("#aircraft-table", DataTable)

        selected_icao = self.selected_aircraft_icao
        selected_row: int | None = None

        table.clear()

        for row_index, aircraft in enumerate(sorted_aircraft):
            table.add_row(
                aircraft.callsign,
                f"{aircraft.altitude_ft:,}",
                f"{aircraft.speed_kt}",
                degrees_to_compass(aircraft.track_deg),
                degrees_to_compass(aircraft.bearing_from_us_deg),
                f"{aircraft.distance_nm:.1f}",
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
            f"AC {receiver_status.aircraft_count} | "
            f"{receiver_status.message_rate:.0f}/s | "
            f"GPS {receiver_status.gps_status} | "
            f"{self.get_sort_indicator()}"
        )

    def set_sort(
        self,
        field: str,
        default_reverse: bool = False,
    ) -> None:
        if self.sort_field == field:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_field = field
            self.sort_reverse = default_reverse

        self.refresh_aircraft()

    def action_sort_distance(self) -> None:
        self.set_sort("DIST")

    def action_sort_altitude(self) -> None:
        self.set_sort("ALT", default_reverse=True)

    def action_sort_callsign(self) -> None:
        self.set_sort("CALL")

    def action_sort_seen(self) -> None:
        self.set_sort("SEEN")

    def action_refresh(self) -> None:
        self.refresh_aircraft()

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


if __name__ == "__main__":
    PocketADSB().run()