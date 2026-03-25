import math
from typing import Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance in meters between two GPS coordinates
    using the Haversine formula.
    """
    R = 6371000  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def is_within_zone(
    student_lat: float,
    student_lng: float,
    zone_lat: float,
    zone_lng: float,
    radius_m: int,
) -> Tuple[bool, float]:
    """
    Check whether a student's GPS coordinate is within the allowed class zone.

    Returns:
        (within_zone: bool, distance_meters: float)
    """
    distance = haversine_distance(student_lat, student_lng, zone_lat, zone_lng)
    return distance <= radius_m, round(distance, 2)
