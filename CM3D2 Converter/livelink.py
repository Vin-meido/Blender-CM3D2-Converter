from __future__ import annotations

import bpy
import os
from pathlib import Path
import sys
import tempfile
from typing import TYPE_CHECKING, Literal, overload

from . import common
from . import compat
from .anm_export import AnmBuilder

from . import Managed
from COM3D2.LiveLink import *
from CM3D2.Serialization import CM3D2Serializer
from System.IO import MemoryStream

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



active_livelink_core: LiveLinkCore = None

@compat.BlRegister()
class VIEW3D_PT_com3d2_livelink(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport under the "Vaporwave" tab"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "COM3D2"
    bl_label = "LiveLink"
    
    def draw(self, context):
        self.layout.operator(LIVELINK_OT_start_server.bl_idname)
        self.layout.operator(LIVELINK_OT_send_animation.bl_idname)
        self.layout.operator(LIVELINK_OT_link_pose.bl_idname)


@compat.BlRegister()
class LIVELINK_OT_start_server(bpy.types.Operator):
    """Embed the data for vaporwave wireframe into the active UV slot"""
    bl_idname = "com3d2livelink.start_server"
    bl_label = "Start LiveLink"

    address = bpy.props.StringProperty("Address", default='com3d2.livelink')
    wait_for_connection = bpy.props.BoolProperty("Wait For Connection", default=True)
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global active_livelink_core
        
        active_livelink_core = LiveLinkCore()
        active_livelink_core.StartServer(self.address)
        if self.wait_for_connection:
            active_livelink_core.WaitForConnection()
        
        return {'FINISHED'}


@compat.BlRegister()
class LIVELINK_OT_wait_for_connection(bpy.types.Operator):
    """Embed the data for vaporwave wireframe into the active UV slot"""
    bl_idname = 'com3d2livelink.wait_for_connection'
    bl_label = "Wait for Connection"
    
    @classmethod
    def poll(cls, context):
        global active_livelink_core
        if not active_livelink_core:
            return False
        return True

    def execute(self, context):
        global active_livelink_core
        
        active_livelink_core.WaitForConnection()
        
        return {'FINISHED'}


@compat.BlRegister()
class LIVELINK_OT_send_animation(bpy.types.Operator):
    """Embed the data for vaporwave wireframe into the active UV slot"""
    bl_idname = "com3d2livelink.send_animation"
    bl_label = "Send Animation"

    @classmethod
    def poll(cls, context):
        global active_livelink_core
        if not active_livelink_core or not active_livelink_core.IsConnected:
            return False
        
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


@compat.BlRegister()
class LIVELINK_OT_link_pose(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = 'com3d2livelink.link_pose'
    bl_label = "Link Pose"
    bl_options = {'UNDO'}
    
    timer = None
    
    @classmethod
    def poll(cls, context):
        global active_livelink_core
        if not active_livelink_core or not active_livelink_core.IsConnected:
            return False
        obj: bpy.types.Object = context.active_object
        return obj and obj.type == 'ARMATURE' and obj.mode == 'POSE'
        
    def modal(self, context, event):
        global active_livelink_core
        
        if not self.poll(context):
            self.cancel(context)
            return {'CANCELLED'}
        
        if event.type == 'TIMER':
            self.update_pose(context)
            
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm: bpy.types.WindowManager = context.window_manager
        self.timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        self.update_pose(context)
        return {'RUNNING_MODAL'}

    def update_pose(self, context: bpy.types.Context):
        global active_livelink_core
        
        builder = AnmBuilder()
        builder.frame_start         = context.scene.frame_current
        builder.frame_end           = context.scene.frame_current
        builder.export_method       = 'ALL'
        builder.is_visual_transform = True
        
        anm = builder.build_anm(context)
        
        serializer = CM3D2Serializer()
        memory_stream = MemoryStream()
        serializer.Serialize(memory_stream, anm)
        active_livelink_core.SendBytes(memory_stream.GetBuffer(), memory_stream.Length)
        active_livelink_core.Flush()
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self.timer)
        

