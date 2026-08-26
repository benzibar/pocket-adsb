from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static

from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.utils.compass import degrees_to_compass


class AircraftDetailScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.pop_screen", "Back"),
    ]

    CSS = """
    #detail {
        padding: 1 2;
    }

    #callsign {
        text-style: bold;
        margin-bottom: 1;
    }

    #columns {
        height: auto;
    }

    .detail-column {
        width: 1fr;
        padding-right: 2;
    }

    #route {
        margin-top: 1;
        margin-bottom: 1;
    }

    #message-details {
        margin-top: 1;
    }
    """

    def __init__(self, aircraft: Aircraft) -> None:
        super().__init__()
        self.aircraft_icao = aircraft.icao
        self.aircraft = aircraft

    def compose(self) -> ComposeResult:
        with Vertical(id="detail"):
            yield Static("", id="callsign")

            with Horizontal(id="columns"):
                with Vertical(classes="detail-column"):
                    yield Static("", id="aircraft-details")

                with Vertical(classes="detail-column"):
                    yield Static("", id="flight-details")

            yield Static("", id="route")
            yield Static("", id="message-details")

        yield Footer()

    def on_mount(self) -> None:
        self.update_display()
        self.set_interval(1.0, self.update_display)

    def update_display(self) -> None:
        # Get the latest version of this aircraft from the main app.
        aircraft = next(
            (
                item
                for item in self.app.aircraft
                if item.icao == self.aircraft_icao
            ),
            None,
        )

        if aircraft is None:
            self.query_one("#callsign", Static).update(
                f"{self.aircraft.callsign} - SIGNAL LOST"
            )
            return

        self.aircraft = aircraft

        selected_altitude = (
            f"{aircraft.selected_altitude_ft:,} ft"
            if aircraft.selected_altitude_ft is not None
            else "---"
        )

        vertical_rate = f"{aircraft.vertical_rate_fpm:+,} fpm"

        self.query_one("#callsign", Static).update(
            aircraft.callsign
        )

        self.query_one("#aircraft-details", Static).update(
            "AIRCRAFT\n"
            f"\nRegistration: {aircraft.registration}"
            f"\nType:         {aircraft.aircraft_type}"
            f"\nCategory:     {aircraft.category}"
            f"\nCountry:      {aircraft.country}"
            f"\nICAO:         {aircraft.icao}"
            f"\nAirline:      {aircraft.airline}"
            f"\nOperator:     {aircraft.operator}"
            f"\nSquawk:       {aircraft.squawk}"
        )

        self.query_one("#flight-details", Static).update(
            "FLIGHT\n"
            f"\nAltitude:     {aircraft.altitude_ft:,} ft"
            f"\nSelected:     {selected_altitude}"
            f"\nSpeed:        {aircraft.speed_kt} kt"
            f"\nVert rate:    {vertical_rate}"
            f"\nTrack:        "
            f"{degrees_to_compass(aircraft.track_deg)} "
            f"({aircraft.track_deg:03d}°)"
            f"\nBearing:      "
            f"{degrees_to_compass(aircraft.bearing_from_us_deg)} "
            f"({aircraft.bearing_from_us_deg:03d}°)"
            f"\nDistance:     {aircraft.distance_nm:.1f} nm"
        )

        self.query_one("#route", Static).update(
            f"ROUTE\n{aircraft.origin}  >  {aircraft.destination}"
        )

        self.query_one("#message-details", Static).update(
            f"Last message:   {aircraft.seen_seconds:.1f}s ago"
            f"\nLast position:  {aircraft.seen_pos_seconds:.1f}s ago"
        )