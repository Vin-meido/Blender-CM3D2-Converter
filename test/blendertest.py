from unittest import TestCase
from pathlib import Path

class BlenderTestCase(TestCase):
    is_cm3d2converter_registered = False
    
    @property
    def cm3d2converter_directory(self) -> Path:
        project_dir = Path(__file__).parent.parent
        if (project_dir / 'CM3D2_Converter').exists():
            return project_dir / 'CM3D2_Converter'
        else:
            return project_dir / 'CM3D2 Converter'

    @property
    def blend_file_path(self) -> str:
        return str(self.cm3d2converter_directory / 'append_data.blend')

    @property
    def resources_dir(self) -> str:
        return str(Path(__file__).parent / 'resources')

    @property
    def output_dir(self) -> str:
        return str(Path(__file__).parent / 'output')
        
    def setUp(self):
        super().setUp()
        import bpy
        bpy.ops.wm.open_mainfile(filepath=self.blend_file_path)
        #if not BlenderTestCase.is_cm3d2converter_registered:
        #    cm3d2converter.register()
        #    cm3d2converter.common.preferences().backup_ext = ''
        #    BlenderTestCase.is_cm3d2converter_registere = True
        
class BlenderTest(BlenderTestCase):
    
    def test_register(self):
        import sys
        import importlib
        sys.path.append(self.cm3d2converter_directory.parent)
        cm3d2converter = importlib.import_module(self.cm3d2converter_directory.name)
        cm3d2converter.register()
    
