import math
from datetime import datetime
from typing import Optional

# Predefined Campus Locations
CAMPUS_LOCATIONS = [
    "Library",
    "Cafeteria",
    "Classroom",
    "Laboratory",
    "Auditorium",
    "Hostel",
    "Parking",
    "Sports Ground",
    "Main Gate",
    "Other"
]

# Campus Zone adjacency matrix
# 1.0: exact same location
# 0.75 - 0.85: neighboring or related zone
# 0.40 - 0.50: general campus distance
# 0.20: remote/different zones
CAMPUS_PROXIMITY_MAP = {
    ("Library", "Classroom"): 0.80,
    ("Library", "Laboratory"): 0.75,
    ("Library", "Cafeteria"): 0.65,
    ("Classroom", "Laboratory"): 0.85,
    ("Cafeteria", "Auditorium"): 0.75,
    ("Hostel", "Sports Ground"): 0.60,
    ("Main Gate", "Parking"): 0.80,
    ("Hostel", "Cafeteria"): 0.70,
}

def calculate_location_similarity(
    loc1: str,
    loc2: str,
    lat1: Optional[float] = None,
    lon1: Optional[float] = None,
    lat2: Optional[float] = None,
    lon2: Optional[float] = None
) -> float:
    """
    Calculates spatial similarity between two campus locations.
    Uses GPS coordinate Haversine distance if available, otherwise zone proximity matrix.
    """
    if not loc1 or not loc2:
        return 0.3

    l1 = loc1.strip().title()
    l2 = loc2.strip().title()

    if l1 == l2:
        return 1.0

    # If GPS coordinates are provided, use Haversine decay
    if lat1 is not None and lon1 is not None and lat2 is not None and lon2 is not None:
        try:
            # Haversine formula
            R = 6371000  # meters
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)

            a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist_meters = R * c

            # Campus scale: within 50m = 0.95, within 200m = 0.80, within 1km = 0.40
            score = math.exp(-dist_meters / 300.0)
            return round(max(0.1, min(1.0, score)), 3)
        except Exception:
            pass

    # Check proximity matrix
    pair = (l1, l2)
    rev_pair = (l2, l1)
    if pair in CAMPUS_PROXIMITY_MAP:
        return CAMPUS_PROXIMITY_MAP[pair]
    if rev_pair in CAMPUS_PROXIMITY_MAP:
        return CAMPUS_PROXIMITY_MAP[rev_pair]

    return 0.35

def calculate_time_similarity(
    date1_str: str,
    time1_str: str,
    date2_str: str,
    time2_str: str
) -> float:
    """
    Calculates contextual temporal similarity between lost and found event timestamps.
    """
    try:
        t1_parts = time1_str.split(":")[:2]
        t2_parts = time2_str.split(":")[:2]
        dt1 = datetime.strptime(f"{date1_str} {t1_parts[0]}:{t1_parts[1]}", "%Y-%m-%d %H:%M")
        dt2 = datetime.strptime(f"{date2_str} {t2_parts[0]}:{t2_parts[1]}", "%Y-%m-%d %H:%M")

        # Time difference in hours
        diff_hours = abs((dt2 - dt1).total_seconds()) / 3600.0

        # Found should ideally be after lost, but allow slight discrepancy for reporting estimation
        if diff_hours <= 6:
            return 1.0
        elif diff_hours <= 24:
            return 0.90
        elif diff_hours <= 48:
            return 0.80
        elif diff_hours <= 72:
            return 0.70
        elif diff_hours <= 168:  # 7 days
            return 0.55
        elif diff_hours <= 720:  # 30 days
            return 0.35
        else:
            return 0.15
    except Exception as e:
        # Fallback date only comparison
        try:
            d1 = datetime.strptime(date1_str, "%Y-%m-%d")
            d2 = datetime.strptime(date2_str, "%Y-%m-%d")
            days_diff = abs((d2 - d1).days)
            if days_diff == 0:
                return 0.95
            elif days_diff <= 2:
                return 0.80
            elif days_diff <= 7:
                return 0.60
            else:
                return 0.30
        except Exception:
            return 0.50
