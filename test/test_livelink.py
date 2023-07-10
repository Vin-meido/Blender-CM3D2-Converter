from blendertest import BlenderTestCase

import bpy

class TestLiveLink(BlenderTestCase):
    
    def test_send_animation(self):
        tpose_object: bpy.types.Object = bpy.data.objects.get('Tスタンス素体.armature')
        bpy.context.view_layer.objects.active = tpose_object
        
        bpy.ops.com3d2livelink.start_livelink()
        bpy.ops.com3d2livelink.send_animation()
        