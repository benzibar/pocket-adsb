import math

from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.ui.aircraft_detail import AircraftDetailScreen
from pocket_adsb.utils.compass import degrees_to_compass
from pocket_adsb.utils.formatting import (
    format_altitude,
    format_distance,
)


class RadarScreen(Screen):
    BINDINGS = [
        ("x", "close_radar", "Table"),
        ("r", "cycle_range", "Range"),
        ("up", "previous_aircraft", "Prev"),
        ("down", "next_aircraft", "Next"),
        ("enter", "open_details", "Details"),
        ("escape", "close_radar", "Table"),
        ("q", "app.quit", "Quit"),
    ]

    RANGES_NM = [
        10,
        25,
        50,
        100,
        200,
    ]

    CSS = """
    #radar-canvas {
        height: 1fr;
        width: 100%;
        padding: 0;
    }

    #radar-status {
        height: 1;
        padding: 0 1;
    }

    #radar-footer {
        height: 1;
        dock: bottom;
        content-align: center middle;
    }
    """

    def __init__(
        self,
        selected_icao: str | None = None,
    ) -> None:
        super().__init__()

        self.selected_icao = selected_icao
        self.range_nm = 100
        self._initial_range_set = False

    def compose(self) -> ComposeResult:
        yield Static(
            "",
            id="radar-canvas",
        )

        yield Static(
            "",
            id="radar-status",
        )

        yield Static(
            "X Table  R Range  Up/Down Select  Enter Details",
            id="radar-footer",
        )

    def on_mount(self) -> None:
        self._choose_initial_range()
        self._ensure_selection()

        self.update_radar()

        self.set_interval(
            1.0,
            self.update_radar,
        )

    def on_resize(self) -> None:
        self.update_radar()

    def _aircraft_in_range(
        self,
    ) -> list[Aircraft]:
        aircraft_list = []

        for aircraft in self.app.aircraft:
            if (
                aircraft.distance_nm is None
                or aircraft.bearing_from_us_deg is None
            ):
                continue

            if aircraft.distance_nm > self.range_nm:
                continue

            aircraft_list.append(
                aircraft
            )

        return sorted(
            aircraft_list,
            key=lambda item: (
                item.distance_nm
                if item.distance_nm is not None
                else float("inf")
            ),
        )

    def _choose_initial_range(self) -> None:
        if self._initial_range_set:
            return

        distances = [
            aircraft.distance_nm
            for aircraft in self.app.aircraft
            if aircraft.distance_nm is not None
        ]

        if not distances:
            self.range_nm = 100
            self._initial_range_set = True
            return

        furthest = min(
            max(distances),
            self.RANGES_NM[-1],
        )

        for range_nm in self.RANGES_NM:
            if furthest <= range_nm:
                self.range_nm = range_nm
                break
        else:
            self.range_nm = self.RANGES_NM[-1]

        self._initial_range_set = True

    def _ensure_selection(self) -> None:
        aircraft_list = self._aircraft_in_range()

        if not aircraft_list:
            self.selected_icao = None
            return

        if self.selected_icao is not None:
            if any(
                aircraft.icao == self.selected_icao
                for aircraft in aircraft_list
            ):
                return

        self.selected_icao = aircraft_list[0].icao
        self.app.selected_aircraft_icao = self.selected_icao

    def _selected_aircraft(
        self,
    ) -> Aircraft | None:
        if self.selected_icao is None:
            return None

        return next(
            (
                aircraft
                for aircraft in self.app.aircraft
                if aircraft.icao == self.selected_icao
            ),
            None,
        )

    def update_radar(self) -> None:
        self._ensure_selection()

        canvas = self.query_one(
            "#radar-canvas",
            Static,
        )

        width = max(
            canvas.size.width,
            20,
        )

        height = max(
            canvas.size.height,
            10,
        )

        grid = [
            [" " for _ in range(width)]
            for _ in range(height)
        ]

        centre_x = width // 2
        centre_y = height // 2

        radius_x = max(
            5,
            centre_x - 6,
        )

        radius_y = max(
            3,
            centre_y - 2,
        )

        self._draw_axes(
            grid,
            centre_x,
            centre_y,
            radius_x,
            radius_y,
        )

        self._draw_range_ticks(
            grid,
            centre_x,
            centre_y,
            radius_x,
            radius_y,
        )

        self._draw_cardinals(
            grid,
            centre_x,
            centre_y,
            radius_x,
            radius_y,
        )

        bold_spans, military_spans = self._plot_aircraft(
            grid,
            centre_x,
            centre_y,
            radius_x,
            radius_y,
        )

        # Our own position.
        grid[centre_y][centre_x] = "+"

        rendered = "\n".join(
            "".join(row)
            for row in grid
        )

        radar_text = Text(rendered)

        for start_x, start_y, length in military_spans:
            start = (
                start_y * (width + 1)
                + start_x
            )

            radar_text.stylize(
                "bright_green",
                start,
                start + length,
            )

        for start_x, start_y, length in bold_spans:
            start = (
                start_y * (width + 1)
                + start_x
            )

            radar_text.stylize(
                "bold",
                start,
                start + length,
            )

        canvas.update(radar_text)
        self._update_status()

    def _draw_axes(
        self,
        grid: list[list[str]],
        centre_x: int,
        centre_y: int,
        radius_x: int,
        radius_y: int,
    ) -> None:
        width = len(grid[0])
        height = len(grid)

        for x in range(
            max(0, centre_x - radius_x),
            min(width, centre_x + radius_x + 1),
        ):
            grid[centre_y][x] = "-"

        for y in range(
            max(0, centre_y - radius_y),
            min(height, centre_y + radius_y + 1),
        ):
            grid[y][centre_x] = "|"

    def _draw_range_ticks(
        self,
        grid: list[list[str]],
        centre_x: int,
        centre_y: int,
        radius_x: int,
        radius_y: int,
    ) -> None:
        fractions = (
            0.25,
            0.50,
            0.75,
            1.00,
        )

        width = len(grid[0])
        height = len(grid)

        for index, fraction in enumerate(
            fractions,
            start=1,
        ):
            horizontal_offset = round(
                radius_x * fraction
            )

            vertical_offset = round(
                radius_y * fraction
            )

            west_x = centre_x - horizontal_offset
            east_x = centre_x + horizontal_offset
            north_y = centre_y - vertical_offset
            south_y = centre_y + vertical_offset

            if 0 <= west_x < width:
                grid[centre_y][west_x] = "+"

            if 0 <= east_x < width:
                grid[centre_y][east_x] = "+"

            if 0 <= north_y < height:
                grid[north_y][centre_x] = "+"

            if 0 <= south_y < height:
                grid[south_y][centre_x] = "+"

            # Label only 50% and 100%.
            if index % 2 != 0:
                continue

            range_value = round(
                self.range_nm * fraction
            )

            label = str(range_value)

            if fraction == 1.0:
                self._write_text(
                    grid,
                    west_x + 2,
                    centre_y,
                    label,
                )

                self._write_text(
                    grid,
                    east_x - len(label) - 1,
                    centre_y,
                    label,
                )

            else:
                self._write_text(
                    grid,
                    west_x - len(label) - 1,
                    centre_y,
                    label,
                )

                self._write_text(
                    grid,
                    east_x + 2,
                    centre_y,
                    label,
                )

            self._write_text(
                grid,
                centre_x + 2,
                north_y,
                label,
            )

            self._write_text(
                grid,
                centre_x + 2,
                south_y,
                label,
            )

    def _draw_cardinals(
        self,
        grid: list[list[str]],
        centre_x: int,
        centre_y: int,
        radius_x: int,
        radius_y: int,
    ) -> None:
        self._write_text(
            grid,
            centre_x,
            max(
                0,
                centre_y - radius_y - 1,
            ),
            "N",
        )

        self._write_text(
            grid,
            centre_x,
            min(
                len(grid) - 1,
                centre_y + radius_y + 1,
            ),
            "S",
        )

        self._write_text(
            grid,
            max(
                0,
                centre_x - radius_x - 2,
            ),
            centre_y,
            "W",
        )

        self._write_text(
            grid,
            min(
                len(grid[0]) - 1,
                centre_x + radius_x + 1,
            ),
            centre_y,
            "E",
        )

    def _plot_aircraft(
        self,
        grid: list[list[str]],
        centre_x: int,
        centre_y: int,
        radius_x: int,
        radius_y: int,
    ) -> tuple[
        list[tuple[int, int, int]],
        list[tuple[int, int, int]],
    ]:
        width = len(grid[0])
        height = len(grid)

        bold_spans: list[
            tuple[int, int, int]
        ] = []

        military_spans: list[
            tuple[int, int, int]
        ] = []

        plotted: list[
            tuple[
                Aircraft,
                int,
                int,
            ]
        ] = []

        # Calculate all aircraft positions first.
        for aircraft in self._aircraft_in_range():
            if (
                aircraft.distance_nm is None
                or aircraft.bearing_from_us_deg is None
            ):
                continue

            range_fraction = (
                aircraft.distance_nm
                / self.range_nm
            )

            angle = math.radians(
                aircraft.bearing_from_us_deg
            )

            x = round(
                centre_x
                + math.sin(angle)
                * radius_x
                * range_fraction
            )

            y = round(
                centre_y
                - math.cos(angle)
                * radius_y
                * range_fraction
            )

            if not (
                0 <= x < width
                and 0 <= y < height
            ):
                continue

            plotted.append(
                (
                    aircraft,
                    x,
                    y,
                )
            )

        # -------------------------------------------------
        # Draw ALL position markers first.
        #
        # Crucially, x/y always represents the CENTRE
        # character of the three-character marker:
        #
        #     (•)
        #      ^
        #
        # and:
        #
        #     [*]
        #      ^
        #
        # Selection therefore cannot change the aircraft's
        # plotted position.
        # -------------------------------------------------

        for aircraft, x, y in plotted:
            is_selected = (
                aircraft.icao
                == self.selected_icao
            )

            marker = (
                "[*]"
                if is_selected
                else "(•)"
            )

            marker_x = x - 1

            self._write_text(
                grid,
                marker_x,
                y,
                marker,
            )

            if aircraft.is_military:
                military_spans.append(
                    (
                        marker_x,
                        y,
                        len(marker),
                    )
                )

            if is_selected:
                bold_spans.append(
                    (
                        marker_x,
                        y,
                        len(marker),
                    )
                )

        # -------------------------------------------------
        # Draw labels independently of position markers.
        # -------------------------------------------------

        for aircraft, x, y in plotted:
            callsign = (
                aircraft.callsign
                or aircraft.icao
            )

            direction = self._track_direction(
                aircraft.track_deg
            )

            label = (
                f"{callsign} - {direction}"
            )

            is_selected = (
                aircraft.icao
                == self.selected_icao
            )

            label_x, label_y = (
                self._choose_aircraft_label_position(
                    grid,
                    x,
                    y,
                    label,
                )
            )

            self._write_text(
                grid,
                label_x,
                label_y,
                label,
            )

            if aircraft.is_military:
                military_spans.append(
                    (
                        label_x,
                        label_y,
                        len(label),
                    )
                )

            if is_selected:
                bold_spans.append(
                    (
                        label_x,
                        label_y,
                        len(label),
                    )
                )

        return bold_spans, military_spans

    def _choose_aircraft_label_position(
        self,
        grid: list[list[str]],
        aircraft_x: int,
        aircraft_y: int,
        label: str,
    ) -> tuple[int, int]:
        """
        Position the descriptive label independently
        from the aircraft's actual position marker.

        The marker itself never moves.

        Preferred layout:

            (•) CALLSIGN - NE
             ^
             exact aircraft coordinate

        If there isn't room, the text can move while
        the marker remains fixed.
        """

        width = len(grid[0])
        height = len(grid)

        label_length = len(label)

        # Marker occupies:
        #
        # aircraft_x - 1
        # aircraft_x
        # aircraft_x + 1
        #
        # Leave one blank column after it.
        right_x = aircraft_x + 3

        # Left-side label ends one column before marker.
        left_x = (
            aircraft_x
            - 3
            - label_length
        )

        candidates = [
            # Same row, right of marker.
            (
                right_x,
                aircraft_y,
            ),

            # Same row, left of marker.
            (
                left_x,
                aircraft_y,
            ),

            # One row below, right.
            (
                right_x,
                aircraft_y + 1,
            ),

            # One row below, left.
            (
                left_x,
                aircraft_y + 1,
            ),

            # One row above, right.
            (
                right_x,
                aircraft_y - 1,
            ),

            # One row above, left.
            (
                left_x,
                aircraft_y - 1,
            ),
        ]

        best_position: tuple[int, int] | None = None
        best_score: int | None = None

        for candidate_x, candidate_y in candidates:
            if not (
                0 <= candidate_y < height
            ):
                continue

            if candidate_x < 0:
                continue

            if (
                candidate_x
                + label_length
                > width
            ):
                continue

            score = 0

            for offset in range(
                label_length
            ):
                existing = grid[
                    candidate_y
                ][
                    candidate_x + offset
                ]

                if existing != " ":
                    score += 1

            if (
                best_score is None
                or score < best_score
            ):
                best_score = score
                best_position = (
                    candidate_x,
                    candidate_y,
                )

                if score == 0:
                    break

        if best_position is not None:
            return best_position

        # Last resort: fit the label on screen.
        fallback_x = min(
            max(
                right_x,
                0,
            ),
            max(
                0,
                width - label_length,
            ),
        )

        fallback_y = min(
            max(
                aircraft_y,
                0,
            ),
            height - 1,
        )

        return (
            fallback_x,
            fallback_y,
        )

    @staticmethod
    def _track_direction(
        track_deg: float | None,
    ) -> str:
        if track_deg is None:
            return "--"

        track = (
            float(track_deg)
            % 360.0
        )

        index = int(
            (
                track + 22.5
            )
            // 45
        ) % 8

        directions = (
            "N",
            "NE",
            "E",
            "SE",
            "S",
            "SW",
            "W",
            "NW",
        )

        return directions[index]

    def _update_status(self) -> None:
        status = self.query_one(
            "#radar-status",
            Static,
        )

        selected = self._selected_aircraft()

        if selected is None:
            status.update(
                f"RNG {self.range_nm}nm | "
                "No aircraft selected"
            )
            return

        callsign = (
            selected.callsign
            or selected.icao
        )

        bearing = (
            degrees_to_compass(
                selected.bearing_from_us_deg
            )
            if selected.bearing_from_us_deg is not None
            else "---"
        )

        track = (
            degrees_to_compass(
                selected.track_deg
            )
            if selected.track_deg is not None
            else "---"
        )

        distance = format_distance(
            selected.distance_nm
        )

        altitude = format_altitude(
            selected.altitude_ft
        )

        status.update(
            f"RNG {self.range_nm}nm | "
            f"{callsign} | "
            f"BRG {bearing} | "
            f"TRK {track} | "
            f"{distance}nm | "
            f"{altitude}ft"
        )

    def action_cycle_range(self) -> None:
        current_index = (
            self.RANGES_NM.index(
                self.range_nm
            )
            if self.range_nm in self.RANGES_NM
            else 0
        )

        next_index = (
            current_index + 1
        ) % len(
            self.RANGES_NM
        )

        self.range_nm = (
            self.RANGES_NM[
                next_index
            ]
        )

        self._ensure_selection()
        self.update_radar()

    def action_next_aircraft(self) -> None:
        self._move_selection(1)

    def action_previous_aircraft(self) -> None:
        self._move_selection(-1)

    def _move_selection(
        self,
        direction: int,
    ) -> None:
        aircraft_list = (
            self._aircraft_in_range()
        )

        if not aircraft_list:
            return

        current_index = 0

        if self.selected_icao is not None:
            for index, aircraft in enumerate(
                aircraft_list
            ):
                if (
                    aircraft.icao
                    == self.selected_icao
                ):
                    current_index = index
                    break

        new_index = (
            current_index + direction
        ) % len(
            aircraft_list
        )

        self.selected_icao = (
            aircraft_list[
                new_index
            ].icao
        )

        self.app.selected_aircraft_icao = (
            self.selected_icao
        )

        self.update_radar()

    def action_open_details(self) -> None:
        aircraft = (
            self._selected_aircraft()
        )

        if aircraft is not None:
            self.app.push_screen(
                AircraftDetailScreen(
                    aircraft
                )
            )

    def action_close_radar(self) -> None:
        self.app.pop_screen()

    @staticmethod
    def _write_text(
        grid: list[list[str]],
        x: int,
        y: int,
        text: str,
    ) -> None:
        if not (
            0 <= y < len(grid)
        ):
            return

        width = len(grid[y])

        for offset, character in enumerate(
            text
        ):
            position = x + offset

            if 0 <= position < width:
                grid[y][position] = character