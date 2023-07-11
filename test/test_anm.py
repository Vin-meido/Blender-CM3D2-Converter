import bpy

from blendertest import BlenderTestCase

class AnmExportTest(BlenderTestCase):

    @staticmethod
    def activate_object(obj: bpy.types.Object):
        collections: list[bpy.types.LayerCollection] = obj.users_collection
        layer_collection = None
        for child in bpy.context.view_layer.layer_collection.children:
            child: bpy.types.LayerCollection
            if child.collection.name == collections[0].name:
                layer_collection = child
                break
        print(layer_collection)
        bpy.context.view_layer.active_layer_collection = layer_collection
        layer_collection.hide_viewport = False
        layer_collection.exclude = False
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = obj
        

    def test_anm_import(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)
        bpy.ops.import_anim.import_cm3d2_anm(filepath=f'{self.resources_dir}/tpose.anm')

    def test_anm_export(self):
        tpose_object: bpy.types.Object = bpy.data.objects.get('Tスタンス素体.armature')
        self.activate_object(tpose_object)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=f'{self.output_dir}/tpose_export_test.anm')
        
    def test_anm_recursive(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)
        
        in_file = f'{self.resources_dir}/tpose.anm'
        out_file_0 = f'{self.output_dir}/test_anm_recursive_0.anm'
        out_file_1 = f'{self.output_dir}/test_anm_recursive_1.anm'
        out_file_2 = f'{self.output_dir}/test_anm_recursive_2.anm'
        
        bpy.ops.import_anim.import_cm3d2_anm(filepath=in_file)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_0)
        bpy.ops.import_anim.import_cm3d2_anm(filepath=out_file_0)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_1)
        bpy.ops.import_anim.import_cm3d2_anm(filepath=out_file_1)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_2)
        
        with open(in_file, 'rb') as reader:
            expected_data = reader.read()
        with open(out_file_0, 'rb') as reader:
            actual_data_0 = reader.read()
        with open(out_file_1, 'rb') as reader:
            actual_data_1 = reader.read()
        with open(out_file_2, 'rb') as reader:
            actual_data_2 = reader.read()
        print(len(expected_data))
        print(len(actual_data_0))
        print(len(actual_data_1))
        print(len(actual_data_2))

