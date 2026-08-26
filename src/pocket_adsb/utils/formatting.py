def format_altitude(value: int | None) -> str:
    if value is None:
        return "---"
    return f"{value:,}"


def format_speed(value: float | None) -> str:
    if value is None:
        return "---"
    return f"{value:.0f}"


def format_distance(value: float | None) -> str:
    if value is None:
        return "---"
    return f"{value:.1f}"


def format_direction(value: float | None) -> str:
    if value is None:
        return "---"

    from pocket_adsb.utils.compass import degrees_to_compass

    return degrees_to_compass(value)


def format_direction_detail(value: float | None) -> str:
    if value is None:
        return "---"

    from pocket_adsb.utils.compass import degrees_to_compass

    return f"{degrees_to_compass(value)} ({value:03.0f}°)"


def format_vertical_rate(value: int | None) -> str:
    if value is None:
        return "---"
    return f"{value:+,} fpm"


def format_seen(value: float | None) -> str:
    if value is None:
        return "---"
    return f"{value:.1f}s"


def format_text(value: str) -> str:
    return value if value else "---"