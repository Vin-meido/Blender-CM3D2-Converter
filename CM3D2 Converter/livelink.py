from __future__ import annotations

import bpy
import os
from pathlib import Path
import sys
import tempfile
from typing import TYPE_CHECKING, Literal, overload

from . import common
from . import compat
from . anm_export import AnmBuilder

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
class COM3D2LiveLinkSettings(bpy.types.PropertyGroup):
    send_animation_max_frames = bpy.props.IntProperty(name="Maximum Frames to Send", default=500, min=1, soft_max=10000)


@compat.BlRegister()
class COM3D2LiveLinkState(bpy.types.PropertyGroup):
    is_link_pose = bpy.props.BoolProperty("Link Pose is Active", default=False, options={'SKIP_SAVE'})
    
    @staticmethod
    def get_active_core() -> LiveLinkCore:
        global active_livelink_core
        return active_livelink_core
    
    @staticmethod
    def set_active_core(value: LiveLinkCore):
        global active_livelink_core
        active_livelink_core = value
    


@compat.BlRegister()
class VIEW3D_PT_com3d2_livelink(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport under the "Vaporwave" tab"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "COM3D2"
    bl_label = "LiveLink"
    
    def __init__(self):
        super().__init__()
    
    def draw(self, context):
        wm = context.window_manager
        core = COM3D2LiveLinkState.get_active_core()
        
        wm = context.window_manager
        
        layout = self.layout
        
        if core is None or not core.IsServer:
            layout.operator(COM3D2LIVELINK_OT_start_server.bl_idname)
        else:
            layout.operator(COM3D2LIVELINK_OT_stop_server.bl_idname)
        
        layout.separator()
        
        if not wm.com3d2_livelink_state.is_link_pose:
            layout.operator(COM3D2LIVELINK_OT_link_pose.bl_idname)
        else:
            layout.operator(COM3D2LIVELINK_OT_unlink_pose.bl_idname)

        layout.separator()
        
        col = layout.column()
        col.enabled = bpy.ops.com3d2livelink.send_animation.poll()
        col.prop(wm.com3d2_livelink_settings, 'send_animation_max_frames')
        send_animation_opr = layout.operator(COM3D2LIVELINK_OT_send_animation.bl_idname)
        send_animation_opr.max_frames = wm.com3d2_livelink_settings.send_animation_max_frames


@compat.BlRegister()
class COM3D2LIVELINK_OT_start_server(bpy.types.Operator):
    """Embed the data for vaporwave wireframe into the active UV slot"""
    bl_idname = "com3d2livelink.start_server"
    bl_label = "Start LiveLink"

    address = bpy.props.StringProperty("Address", default='com3d2.livelink')
    wait_for_connection = bpy.props.BoolProperty("Wait For Connection", default=True)
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        core: LiveLinkCore = COM3D2LiveLinkState.get_active_core()
        
        if core and core.IsServer:
            core.Disconnect()
        elif core is None:
            core = LiveLinkCore()
            COM3D2LiveLinkState.set_active_core(core)
        core.StartServer(self.address)
        
        if self.wait_for_connection:
            core.WaitForConnection()
        
        return {'FINISHED'}


@compat.BlRegister()
class COM3D2LIVELINK_OT_stop_server(bpy.types.Operator):
    """Embed the data for vaporwave wireframe into the active UV slot"""
    bl_idname = "com3d2livelink.stop_server"
    bl_label = "Stop LiveLink"
    
    @classmethod
    def poll(cls, context):
        return False  # This currently crashes blender
        global active_livelink_core
        if active_livelink_core is None:
            return False
        return active_livelink_core.IsConnected

    def execute(self, context):
        global active_livelink_core
        active_livelink_core.Disconnect()
        return {'FINISHED'}


@compat.BlRegister()
class COM3D2LIVELINK_OT_wait_for_connection(bpy.types.Operator):
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
class COM3D2LIVELINK_OT_send_animation(bpy.types.Operator):
    """Embed the data for vaporwave wireframe into the active UV slot"""
    bl_idname = "com3d2livelink.send_animation"
    bl_label = "Send Animation"
    
    max_frames = bpy.props.IntProperty(name="Maximum Frames to Send", default=1000, min=1, soft_max=10000)

    @classmethod
    def poll(cls, context):
        global active_livelink_core
        if not active_livelink_core or not active_livelink_core.IsConnected:
            return False
        
        obj = context.active_object
        return obj and obj.type == 'ARMATURE'

    def execute(self, context):
        core: LiveLinkCore = COM3D2LiveLinkState.get_active_core()
        
        if bpy.ops.com3d2livelink.unlink_pose.poll():
            bpy.ops.com3d2livelink.unlink_pose()
            
        current_frame = context.scene.frame_current
        
        builder = AnmBuilder()
        builder.frame_start         = context.scene.frame_current
        builder.frame_end           = min(context.scene.frame_end, builder.frame_start + self.max_frames)
        builder.export_method       = 'ALL'
        builder.is_visual_transform = True
        
        anm = builder.build_anm(context)
        
        serializer = CM3D2Serializer()
        memory_stream = MemoryStream()
        serializer.Serialize(memory_stream, anm)
        core.SendBytes(memory_stream.GetBuffer(), memory_stream.Length)
        core.Flush()
        
        context.scene.frame_current = current_frame
            
        return {'FINISHED'}


@compat.BlRegister()
class COM3D2LIVELINK_OT_link_pose(bpy.types.Operator):
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
        state: COM3D2LiveLinkState = context.window_manager.com3d2_livelink_state
        core = state.get_active_core()
        
        
        if not self.poll(context):
            self.cancel(context)
            return {'CANCELLED'}
        
        if not state.is_link_pose:
            return {'CANCELLED'}
        
        if event.type == 'TIMER':
            self.update_pose(context)
            
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm: bpy.types.WindowManager = context.window_manager
        state: COM3D2LiveLinkState = wm.com3d2_livelink_state
        self.timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        state.is_link_pose = True
        self.update_pose(context)
        return {'RUNNING_MODAL'}

    def update_pose(self, context: bpy.types.Context):
        global active_livelink_core
        
        builder = AnmBuilder()
        builder.no_set_frame        = True
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
        wm: bpy.types.WindowManager = context.window_manager
        state: COM3D2LiveLinkState = wm.com3d2_livelink_state
        wm.event_timer_remove(self.timer)
        state.is_link_pose = False


@compat.BlRegister()
class COM3D2LIVELINK_OT_unlink_pose(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = 'com3d2livelink.unlink_pose'
    bl_label = "Unlink Pose"
    bl_options = {'UNDO'}
    
    timer = None
    
    @classmethod
    def poll(cls, context):
        state = context.window_manager.com3d2_livelink_state
        core: LiveLinkCore = COM3D2LiveLinkState.get_active_core()
        
        if core is None or not core.IsConnected:
            return False
        return state.is_link_pose

    def execute(self, context):
        state = context.window_manager.com3d2_livelink_state
        state.is_link_pose = False
        return {'FINISHED'}

