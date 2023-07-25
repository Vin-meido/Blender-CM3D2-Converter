import bpy
from mathutils import Vector, Quaternion

from blendertest import BlenderTestCase
from profile_helpers import dump_test_stats, Profile, LineProfile

import cm3d2converter

class ModelImportTest(BlenderTestCase):
        

    def test_model_import(self):
        in_file = f'{self.resources_dir}/body001.model'
        bpy.ops.import_mesh.import_cm3d2_model(filepath=in_file)
        
    def test_model_import_dress379(self):
        """Historically caused KeyError in model_import.write_vertex_colors caused by loose vertices."""
        in_file = f'{self.resources_dir}/Dress379_wear.model'
        bpy.ops.import_mesh.import_cm3d2_model(filepath=in_file)

    