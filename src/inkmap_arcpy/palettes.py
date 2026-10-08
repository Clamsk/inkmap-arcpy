from dataclasses import dataclass

ROLES = {"water": "Polygon", "green": "Polygon", "buildings": "Polygon",
         "paper": "Polygon", "roads_main": "Polyline", "roads_other": "Polyline",
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
    paper: tuple = (248, 247, 243)

    def __post_init__(self):
        for key in ("water", "green", "road", "building", "ink", "accent", "paper"):
            value = getattr(self, key)
            if len(value) != 3 or any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 255 for v in value):
                raise ValueError(f"{key} must contain three integer RGB values in 0..255")


PALETTES = {
    "watercolor": Palette("watercolor", (66, 153, 171), (57, 138, 93),
                          (123, 164, 188), (219, 220, 218), (112, 127, 137), (20, 84, 134)),
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
