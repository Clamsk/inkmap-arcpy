import json
import tempfile
import unittest
from pathlib import Path
from inkmap_arcpy.atlas import load_atlas_config,validate_atlas_config
from inkmap_arcpy.layout_primitives import dms


class AtlasConfigTests(unittest.TestCase):
    def job(self):
        return dict(project='input.aprx',map='Map',output_folder='atlas-new',
                    center=[119.294,26.086],scale=21000,title='Gulou',layers={'Water':'water'})

    def test_unsafe_numeric_values_rejected_before_arcpy(self):
        for key,value in [('center',[119,float('nan')]),('scale',True),('dpi',240.5),
                          ('grid_seconds',0),('legend_transparency',101)]:
            job=self.job(); job[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_atlas_config(job)

    def test_unbound_legend_and_bad_opacity_rejected(self):
        job=self.job(); job['legend']=[dict(layer='Absent',label='Water')]
        with self.assertRaises(ValueError): validate_atlas_config(job)
        job=self.job(); job['layers']['Water']=dict(role='water',fill_opacity=-1)
        with self.assertRaises(ValueError): validate_atlas_config(job)

    def test_relative_paths_follow_job_including_locators(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path=Path(folder)/'job.json'; job=self.job()
            job['locators']=[dict(geojson='boundaries.json',caption='China',highlight='350000')]
            path.write_text(json.dumps(job),encoding='utf-8')
            loaded=load_atlas_config(path)
            self.assertEqual(Path(loaded['project']),Path(folder)/'input.aprx')
            self.assertEqual(Path(loaded['locators'][0]['geojson']),Path(folder)/'boundaries.json')

    def test_graticule_hemisphere_and_carry(self):
        self.assertEqual(dms(-119.5,'E'),'119°30′00″W')
        self.assertEqual(dms(-26.5,'N'),'26°30′00″S')
        self.assertEqual(dms(26+59/60+59.9999/3600,'N'),'27°00′00″N')

if __name__=='__main__': unittest.main()
