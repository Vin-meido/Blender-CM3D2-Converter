from blendertest import BlenderTestCase

import bpy
import cm3d2converter

class AnmExportTest(BlenderTestCase):
    
    def test_tpose_export(self):
        tpose_object: bpy.types.Object = bpy.data.objects.get('Tスタンス素体.armature')
        bpy.context.view_layer.objects.active = tpose_object
        bpy.ops.export_anim.export_cm3d2_anm(filepath=f'{self.output_dir}/tpose.anm')
        