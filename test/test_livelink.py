import bpy
import subprocess
import os
from pathlib import Path

from blendertest import BlenderTestCase

class LiveLinkClientCLI:
    exe_path = Path(__file__).parent.parent / 'CM3D2 Converter' / 'Managed' / 'COM3D2.LiveLink.CLI.exe'
    
    def __init__(self, address: str = 'com3d2.livelink'):
        print(self.exe_path)
        self.address = address
        self.process = subprocess.Popen(
            [f'{self.exe_path}', '--client', address],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        

class TestLiveLink(BlenderTestCase):
    
   
    def setUp(self):
        super().setUp()
        self.address = f'com3d2.livelink.{os.getpid()}'
    
    def test_send_animation(self):
        tpose_object: bpy.types.Object = bpy.data.objects.get('Tスタンス素体.armature')
        bpy.context.view_layer.objects.active = tpose_object
        
        print(f"address = {self.address}")
        
        bpy.ops.com3d2livelink.start_server(address=self.address, wait_for_connection=False)
        client = LiveLinkClientCLI(self.address)
        bpy.ops.com3d2livelink.wait_for_connection()
        bpy.ops.com3d2livelink.send_animation()
        
    def test_pose_link(self):
        tpose_object: bpy.types.Object = bpy.data.objects.get('Tスタンス素体.armature')
        bpy.context.view_layer.objects.active = tpose_object
        
        print(f"address = {self.address}")
        
        bpy.ops.com3d2livelink.start_server(address=self.address, wait_for_connection=False)
        client = LiveLinkClientCLI(self.address)
        bpy.ops.com3d2livelink.wait_for_connection()
        bpy.ops.com3d2livelink.send_animation()
        