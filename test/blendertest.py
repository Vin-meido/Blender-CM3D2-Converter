from unittest import TestCase
from typing import TYPE_CHECKING
from pathlib import Path

import bpy
import cm3d2converter

class BlenderTestCase(TestCase):
    @property
    def blend_file_path(self) -> str:
        return str(Path(cm3d2converter.__file__).parent / 'append_data.blend')
    
    @property
    def resources_dir(self) -> str:
        return str(Path(__file__).parent / 'resources')
    
    @property
    def output_dir(self) -> str:
        return str(Path(__file__).parent / 'output')
        
    def setUp(self):
        super().setUp()
        bpy.ops.wm.open_mainfile(filepath=self.blend_file_path)
        cm3d2converter.register()
        cm3d2converter.common.preferences().backup_ext = ''
        
class BlenderTest(BlenderTestCase):
    
    def test_launch(self):
        pass
    
