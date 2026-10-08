"""Small geometry helper for distance rings; no feature data are modified."""
import math


def distance_rings(point_geometry, distances=(500, 1000, 1500)):
    """Return {distance_in_metres: polyline} in a suitable local projected CRS."""
    sr = point_geometry.spatialReference
    if getattr(point_geometry, "type", "").lower() != "point":
        raise ValueError("distance_rings requires a PointGeometry")
    if sr.type != "Projected" or sr.factoryCode in {3857, 3395, 102100, 102113}:
        raise ValueError("Use a suitable local projected CRS for metre distances (not geographic/Web Mercator)")
    units = sr.metersPerUnit
    if not units or not math.isfinite(units) or units <= 0:
        raise ValueError("Spatial reference has no usable metres-per-unit conversion")
    distances = tuple(distances)
    if not distances or len(set(distances)) != len(distances) or any(
            isinstance(d, bool) or not isinstance(d, (int, float)) or not math.isfinite(d) or d <= 0 for d in distances):
        raise ValueError("Distances must be distinct positive finite metre values")
    return {d: point_geometry.buffer(d / units).boundary() for d in distances}
