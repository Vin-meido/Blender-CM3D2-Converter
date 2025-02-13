# 画面右上 (「情報」エリア → ヘッダー)
import bpy
import bmesh
from . import common
from . import compat
from .translations.pgettext_functions import *


# メニュー等に項目追加
def menu_func(self, context):
    self.layout.operator('mesh.vertices_count_checker', icon_value=common.kiss_icon())


@compat.BlRegister()
class CNV_OT_vertices_count_checker(bpy.types.Operator):
    bl_idname = 'mesh.vertices_count_checker'
    bl_label = "頂点数をチェック"
    bl_description = "選択メッシュがConverterで出力可能な頂点数に収まっているかをチェックします"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH'

    def execute(self, context):
        me = context.object.data
        if not me.uv_layers.active:
            self.report(type={'ERROR'}, message="UVが存在しないので測定できません。")
            return {'FINISHED'}
        bm = bmesh.new()
        bm.from_mesh(me)

        alreadys = {}
        uv_lay = bm.loops.layers.uv.active

        for face in bm.faces:
            for loop in face.loops:
                info = (loop.vert.index, loop[uv_lay].uv.x, loop[uv_lay].uv.y)
                if info not in alreadys:
                    alreadys[info] = None
        bm.free()

        inner_count = len(alreadys)
        real_count = len(me.vertices)
        if inner_count <= 65535:
            self.report(type={'INFO'}, message=f_tip_("○ 出力可能な頂点数です、あと約{}頂点ほど余裕があります (頂点数:{}(+{}) UV分割で増加:+{}％)", 65535 - inner_count, real_count, inner_count - real_count, int(inner_count / real_count * 100)))
        else:
            self.report(type={'ERROR'}, message=f_tip_("× 出力できない頂点数です、あと約{}頂点減らしてください (頂点数:{}(+{}) UV分割で増加:+{}％)", inner_count - 65535, real_count, inner_count - real_count, int(inner_count / real_count * 100)))

        return {'FINISHED'}
