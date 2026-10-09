from dataclasses import dataclass

ROLES = {"water": "Polygon", "green": "Polygon", "buildings": "Polygon",
         "paper": "Polygon", "roads_main": "Polyline", "roads_other": "Polyline",
         "walk": "Polyline", "water_line": "Polyline", "residential": "Polygon",
         "plaza": "Polygon", "heritage": "Polygon", "community": "Point", "place_label": "Point",
         "buffer": "Polyline", "boundary": "Polyline", "station": "Point", "site": "Point"}


@dataclass(frozen=True)
class Palette:
    name: str
    water: tuple
    green: tuple
    road: tuple
    building: tuple
    ink: tuple
    accent: tuple
    paper: tuple = (249, 247, 239)
    minor: tuple = (151, 144, 128)
    station: tuple = (88, 115, 119)
    residential: tuple = (159, 147, 124)
    plaza: tuple = (194, 166, 123)
    heritage: tuple = (166, 141, 113)

    def __post_init__(self):
        for key in ("water", "green", "road", "building", "ink", "accent", "paper", "minor", "station", "residential", "plaza", "heritage"):
            value = getattr(self, key)
            if len(value) != 3 or any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 255 for v in value):
                raise ValueError(f"{key} must contain three integer RGB values in 0..255")


PALETTES = {
    "watercolor": Palette("watercolor", (66, 153, 171), (57, 138, 93),
                          (105, 139, 154), (177, 180, 168), (93, 87, 75), (151, 87, 70)),
    "ink": Palette("ink", (125, 151, 153), (135, 148, 129),
                   (161, 163, 159), (224, 223, 216), (73, 80, 78), (59, 69, 67)),
}


def get_palette(value="watercolor"):
    if isinstance(value, Palette):
        return value
    try:
        return PALETTES[value]
    except (KeyError, TypeError):
        raise ValueError(f"Unknown palette {value!r}; choose {', '.join(PALETTES)}") from None
