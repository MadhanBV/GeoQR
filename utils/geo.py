import math
from typing import Tuple


# Earth's mean radius in meters (WGS-84 standard approximation)
EARTH_RADIUS_METERS: float = 6371000.0


def calculate_haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the great-circle distance between two geographic coordinates on Earth
    using the Haversine formula.

    :param lat1: Latitude of point 1 (in decimal degrees)
    :param lon1: Longitude of point 1 (in decimal degrees)
    :param lat2: Latitude of point 2 (in decimal degrees)
    :param lon2: Longitude of point 2 (in decimal degrees)
    :return: Distance between point 1 and point 2 in meters.
    """
    # Convert latitude and longitude from decimal degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula computation
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )

    # Angular distance in radians
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    # Distance in meters
    distance_meters = EARTH_RADIUS_METERS * c
    return round(distance_meters, 2)


def is_within_radius(
    center_lat: float,
    center_lon: float,
    target_lat: float,
    target_lon: float,
    allowed_radius_meters: float
) -> Tuple[bool, float]:
    """
    Check whether a target coordinate is within an allowed radius of a center coordinate.

    :param center_lat: Latitude of event center (organizer location)
    :param center_lon: Longitude of event center
    :param target_lat: Latitude of student's device
    :param target_lon: Longitude of student's device
    :param allowed_radius_meters: Allowed geofence boundary in meters (e.g. 50m, 100m)
    :return: Tuple of (is_within_geofence: bool, actual_distance_meters: float)
    """
    distance = calculate_haversine_distance(center_lat, center_lon, target_lat, target_lon)
    is_valid = distance <= allowed_radius_meters
    return is_valid, distance
