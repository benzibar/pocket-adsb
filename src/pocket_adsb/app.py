from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Footer, Header

from pocket_adsb.services.simulator import AircraftSimulator
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
    """

    def __init__(self) -> None:
        super().__init__()
        self.simulator = AircraftSimulator()

    def compose(self) -> ComposeResult:
        yield Header()

        with Container():
            yield DataTable(id="aircraft-table")

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
)

        self.refresh_aircraft()
        self.set_interval(1.0, self.refresh_aircraft)

    def refresh_aircraft(self) -> None:
        table = self.query_one("#aircraft-table", DataTable)
        aircraft_list = self.simulator.update()

        table.clear()

        for aircraft in aircraft_list:
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
                key=aircraft.icao,
            )

    def action_refresh(self) -> None:
        self.refresh_aircraft()


if __name__ == "__main__":
    PocketADSB().run()