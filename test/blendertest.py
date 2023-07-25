from unittest import TestCase
from typing import TYPE_CHECKING
from pathlib import Path

import bpy
import cm3d2converter

class BlenderTestCase(TestCase):
    is_cm3d2converter_registered = False
    
    @staticmethod
    def activate_object(obj: bpy.types.Object):
        collections: list[bpy.types.LayerCollection] = obj.users_collection
        layer_collection = None
        for child in bpy.context.view_layer.layer_collection.children:
            child: bpy.types.LayerCollection
            if child.collection.name == collections[0].name:
                layer_collection = child
                break
        bpy.context.view_layer.active_layer_collection = layer_collection
        layer_collection.hide_viewport = False
        layer_collection.exclude = False
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = obj
        
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
    
