def degrees_to_compass(degrees: float) -> str:
    """Convert degrees to a 16-point compass direction."""

    directions = (
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    )

    normalized = degrees % 360
    index = int((normalized + 11.25) / 22.5) % 16

    return directions[index]