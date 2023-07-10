from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
from typing import TYPE_CHECKING, Literal, overload

#import pythonnet as clr
import clr

managed_path = Path(__file__).parent / 'Managed'
sys.path.append(str(managed_path))
clr.AddReference('COM3D2.LiveLink')

from COM3D2.LiveLink import *

if TYPE_CHECKING:
    # This stub can be easially generated with https://www.javainuse.com/csharp2py
    
    class LiveLinkCore:
        def __init__(self):
            pass
        @property
        def Address(self):
            pass
        @property
        def IsClient(self):
            pass
        @property
        def IsConnected(self):
            pass
        @property
        def IsServer(self):
            pass
        def Disconnect(self):
            pass
        def Dispose(self):
            pass
        def Flush(self):
            pass
        def ReadAll(self):
            pass
        def ReadString(self):
            pass
        @overload
        def SendBytes(self, bytes):
            pass
        @overload
        def SendBytes(self, bytes, count):
            pass
        def SendString(self, value):
            pass
        def StartClient(self, address = "com3d2.livelink"):
            pass
        def StartServer(self, address = "com3d2.livelink"):
            pass
        def TryReadMessage(self, message):
            pass
        def WaitForConnection(self, timeout = 1000):
            pass

import bpy

from . import common
from . import compat


active_livelink_core: LiveLinkCore = None

@compat.BlRegister()
class VIEW3D_PT_com3d2_livelink(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport under the "Vaporwave" tab"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "COM3D2"
    bl_label = "LiveLink"
    
    def draw(self, context):
        self.layout.operator("com3d2livelink.start_livelink")
        self.layout.operator("com3d2livelink.send_animation")

@compat.BlRegister()
class LIVELINK_OT_start_livelink(bpy.types.Operator):
    """Embed the data for vaporwave wireframe into the active UV slot"""
    bl_idname = "com3d2livelink.start_livelink"
    bl_label = "Start LiveLink"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global active_livelink_core
        
        active_livelink_core = LiveLinkCore()
        active_livelink_core.StartServer()
        active_livelink_core.WaitForConnection()
        
        return {'FINISHED'}

@compat.BlRegister()
class LIVELINK_OT_send_animation(bpy.types.Operator):
    """Embed the data for vaporwave wireframe into the active UV slot"""
    bl_idname = "com3d2livelink.send_animation"
    bl_label = "Send Animation"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE'

    def execute(self, context):
        global active_livelink_core
        
        pre_anm_export_path = common.preferences().anm_export_path
        try:
            temp_file_handle, temp_file_path = tempfile.mkstemp()
            os.close(temp_file_handle)
            
            bpy.ops.export_anim.export_cm3d2_anm(filepath=temp_file_path)
            
            with open(temp_file_path, 'rb') as data:
                active_livelink_core.SendBytes(data.read())
                active_livelink_core.Flush()
            
        finally:
            common.preferences().anm_export_path = pre_anm_export_path
            os.remove(temp_file_path)
            
        return {'FINISHED'}
