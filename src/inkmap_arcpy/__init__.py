"""ArcPy is imported lazily, so palettes/configuration work in normal Python."""
__version__ = "0.4.0"

from .palettes import Palette, get_palette
from .symbols import apply_style
from .workflow import style_project, inspect_project
from .atlas import compose_atlas, load_atlas_config

__all__ = ["Palette", "get_palette", "apply_style", "style_project", "inspect_project", "compose_atlas", "load_atlas_config"]
