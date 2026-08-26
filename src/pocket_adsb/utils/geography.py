import math

from pocket_adsb.models.position import Position


EARTH_RADIUS_NM = 3440.065


def calculate_distance_nm(
    own_position: Position,
    aircraft_latitude: float,
    aircraft_longitude: float,
) -> float:
    lat1 = math.radians(own_position.latitude)
    lon1 = math.radians(own_position.longitude)

    lat2 = math.radians(aircraft_latitude)
    lon2 = math.radians(aircraft_longitude)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return EARTH_RADIUS_NM * c


def calculate_bearing_deg(
    own_position: Position,
    aircraft_latitude: float,
    aircraft_longitude: float,
) -> float:
    lat1 = math.radians(own_position.latitude)
    lat2 = math.radians(aircraft_latitude)

    delta_lon = math.radians(
        aircraft_longitude - own_position.longitude
    )

    x = math.sin(delta_lon) * math.cos(lat2)

    y = (
        math.cos(lat1) * math.sin(lat2)
        - math.sin(lat1)
        * math.cos(lat2)
        * math.cos(delta_lon)
    )

    bearing = math.degrees(math.atan2(x, y))

    return (bearing + 360) % 360