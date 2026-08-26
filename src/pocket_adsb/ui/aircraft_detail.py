from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static

from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.utils.formatting import (
    format_altitude,
    format_direction_detail,
    format_distance,
    format_seen,
    format_speed,
    format_text,
    format_vertical_rate,
)


class AircraftDetailScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.pop_screen", "Back"),
    ]

    CSS = """
    #detail {
        padding: 0 2;
        height: 1fr;
    }

    #callsign {
        height: auto;
        text-style: bold;
        margin-bottom: 1;
    }

    #columns {
        height: auto;
    }

    .detail-column {
        width: 1fr;
        height: auto;
        padding-right: 2;
    }

    #aircraft-details {
        height: auto;
    }

    #flight-details {
        height: auto;
    }

    #route {
        height: auto;
        margin-top: 1;
    }

    #message-details {
        height: auto;
        margin-top: 1;
    }

    #detail-footer {
        height: 1;
        dock: bottom;
        content-align: center middle;
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

        yield Static(
            "Esc Back",
            id="detail-footer",
        )

    def on_mount(self) -> None:
        self.update_display()
        self.set_interval(1.0, self.update_display)

    def update_display(self) -> None:
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
                f"{self.aircraft.callsign or self.aircraft.icao} - SIGNAL LOST"
            )
            return

        self.aircraft = aircraft

        selected_altitude = (
            f"{format_altitude(aircraft.selected_altitude_ft)} ft"
            if aircraft.selected_altitude_ft is not None
            else "---"
        )

        altitude = (
            f"{format_altitude(aircraft.altitude_ft)} ft"
            if aircraft.altitude_ft is not None
            else "---"
        )

        speed = (
            f"{format_speed(aircraft.speed_kt)} kt"
            if aircraft.speed_kt is not None
            else "---"
        )

        distance = (
            f"{format_distance(aircraft.distance_nm)} nm"
            if aircraft.distance_nm is not None
            else "---"
        )

        self.query_one("#callsign", Static).update(
            aircraft.callsign or aircraft.icao
        )

        self.query_one("#aircraft-details", Static).update(
            "AIRCRAFT\n"
            f"\nRegistration: {format_text(aircraft.registration)}"
            f"\nType:         {format_text(aircraft.aircraft_type)}"
            f"\nCategory:     {format_text(aircraft.category)}"
            f"\nCountry:      {format_text(aircraft.country)}"
            f"\nICAO:         {aircraft.icao}"
            f"\nAirline:      {format_text(aircraft.airline)}"
            f"\nOperator:     {format_text(aircraft.operator)}"
            f"\nSquawk:       {format_text(aircraft.squawk)}"
        )

        self.query_one("#flight-details", Static).update(
            "FLIGHT\n"
            f"\nAltitude:     {altitude}"
            f"\nSelected:     {selected_altitude}"
            f"\nSpeed:        {speed}"
            f"\nVert rate:    "
            f"{format_vertical_rate(aircraft.vertical_rate_fpm)}"
            f"\nTrack:        "
            f"{format_direction_detail(aircraft.track_deg)}"
            f"\nBearing:      "
            f"{format_direction_detail(aircraft.bearing_from_us_deg)}"
            f"\nDistance:     {distance}"
        )

        self.query_one("#route", Static).update(
            f"ROUTE   "
            f"{format_text(aircraft.origin)} > "
            f"{format_text(aircraft.destination)}"
        )

        self.query_one("#message-details", Static).update(
            f"Last msg: {format_seen(aircraft.seen_seconds)}   "
            f"Last pos: {format_seen(aircraft.seen_pos_seconds)}"
        )