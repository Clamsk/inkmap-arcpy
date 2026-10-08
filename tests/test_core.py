import json
import tempfile
import unittest
from pathlib import Path
from inkmap_arcpy import Palette, get_palette
from inkmap_arcpy.workflow import load_config, unique


class CoreTests(unittest.TestCase):
    def test_bad_palette_rejected(self):
        with self.assertRaises(ValueError):
            Palette("invalid", (256,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0))
        with self.assertRaises(ValueError):
            get_palette("missing")

    def test_relative_job_paths_follow_config(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            f = Path(folder) / "job.json"
            f.write_text(json.dumps({"project":"input.aprx", "output_project":"out/x.aprx",
                                     "export":{"path":"out/map.png"}}))
            cfg = load_config(f)
            self.assertEqual(Path(cfg["project"]), Path(folder) / "input.aprx")
            self.assertEqual(Path(cfg["export"]["path"]), Path(folder) / "out/map.png")

    def test_ambiguous_layer_names_rejected(self):
        class Layer:
            name = "Water"
            longName = "Group\\Water"
        with self.assertRaises(ValueError):
            unique([Layer(), Layer()], "Group\\Water", "layer")
        self.assertEqual(unique([Layer()], "Group\\Water", "layer").name, "Water")


if __name__ == "__main__":
    unittest.main()
