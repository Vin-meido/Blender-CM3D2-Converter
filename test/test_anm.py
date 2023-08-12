import bpy
from mathutils import Vector, Quaternion

from blendertest import BlenderTestCase
from profile_helpers import dump_test_stats, Profile, LineProfile

import cm3d2converter

class AnmExportTest(BlenderTestCase):
    def test_anm_import(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)
        bpy.ops.import_anim.import_cm3d2_anm(filepath=f'{self.resources_dir}/tpose.anm')

    def test_anm_export(self):
        tpose_object: bpy.types.Object = bpy.data.objects.get('Tスタンス素体.armature')
        self.activate_object(tpose_object)

        bpy.ops.export_anim.export_cm3d2_anm(
            filepath=f'{self.output_dir}/{self._testMethodName}.anm',
            is_backup=False
        )

    def test_anm_recursive(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)

        in_file = f'{self.resources_dir}/tpose.anm'
        out_file_0 = f'{self.output_dir}/{self._testMethodName}_0.anm'
        out_file_1 = f'{self.output_dir}/{self._testMethodName}_1.anm'
        out_file_2 = f'{self.output_dir}/{self._testMethodName}_2.anm'

        bpy.ops.import_anim.import_cm3d2_anm(filepath=in_file)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_0, is_export_scale=True)

        bpy.ops.object.duplicate()
        body001_armature_copy: bpy.types.Object = bpy.data.objects.get('body001.body.armature.001')
        self.activate_object(body001_armature_copy)

        bpy.ops.import_anim.import_cm3d2_anm(filepath=out_file_0)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_1, is_export_scale=True)
        bpy.ops.import_anim.import_cm3d2_anm(filepath=out_file_1)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_2, is_export_scale=True)

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

        # Check the loss
        pose: bpy.types.Pose = body001_armature_object.pose
        pose_copy: bpy.types.Pose = body001_armature_copy.pose
        for bone in pose.bones:
            bone: bpy.types.PoseBone
            bone_copy: bpy.types.PoseBone = pose_copy.bones.get(bone.name)
            if bone_copy is None:
                print(f"Could not find bone {bone.name} in copied armature")
                continue
            loc_diff: Vector = bone_copy.location - bone.location
            rot_diff: Quaternion = bone_copy.rotation_quaternion - bone.rotation_quaternion
            scl_diff: Vector = bone_copy.scale - bone.scale
    
            # TODO : Use a proper epislon-based floating point precision check
            self.assertAlmostEqual(loc_diff.magnitude * 0.01, 0, 1, msg=f"loc diff of {bone.name} is {loc_diff}")
            self.assertAlmostEqual(rot_diff.magnitude * 0.01, 0, 1, msg=f"rot diff of {bone.name} is {rot_diff}")
            self.assertAlmostEqual(scl_diff.magnitude * 0.01, 0, 1, msg=f"scl diff of {bone.name} is {scl_diff}")

    def testprofile_anm_import(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)

        in_file = f'{self.resources_dir}/dance_cm3d21_pole_001_fa_f1.anm'
        in_file = f'{self.resources_dir}/dance_cm3d2_001_zoukin.anm'
        in_file = f'{self.resources_dir}/tpose.anm'

        #with ProfileLog(self.test_anm_recursive.__name__):
        lineprof = LineProfile()
        lineprof.add_module(cm3d2converter.anm_import)
        prof = Profile()
        lineprof.enable()
        prof.enable()

        bpy.ops.import_anim.import_cm3d2_anm(filepath=in_file)

        prof.disable()

        dump_test_stats(self._testMethodName, prof, lineprof)

    def testprofile_anm_export(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)

        in_file = f'{self.resources_dir}/dance_cm3d_001_f1.anm'
        in_file = f'{self.resources_dir}/dance_cm3d21_pole_001_fa_f1.anm'
        in_file = f'{self.resources_dir}/dance_cm3d2_001_zoukin.anm'
        in_file = f'{self.resources_dir}/tpose.anm'
        out_file = f'{self.output_dir}/{self._testMethodName}.anm'


        bpy.ops.import_anim.import_cm3d2_anm(filepath=in_file)

        #with ProfileLog(self.test_anm_recursive.__name__):
        lineprof = LineProfile()
        lineprof.add_module(cm3d2converter.anm_export)
        prof = Profile()
        lineprof.enable()
        prof.enable()

        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file)

        dump_test_stats(self._testMethodName, prof, lineprof)  

    def testprofile_anm_export_with_warmup(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)

        in_file = f'{self.resources_dir}/dance_cm3d_001_f1.anm'
        in_file = f'{self.resources_dir}/dance_cm3d21_pole_001_fa_f1.anm'
        in_file = f'{self.resources_dir}/dance_cm3d2_001_zoukin.anm'
        in_file = f'{self.resources_dir}/tpose.anm'
        out_file = f'{self.output_dir}/{self._testMethodName}.anm'


        bpy.ops.import_anim.import_cm3d2_anm(filepath=in_file)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file)

        #with ProfileLog(self.test_anm_recursive.__name__):
        lineprof = LineProfile()
        lineprof.add_module(cm3d2converter.anm_export)
        prof = Profile()
        lineprof.enable()
        prof.enable()

        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file)

        dump_test_stats(self._testMethodName, prof, lineprof)

    def test_exanm(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)

        bpy.ops.object.duplicate()
        body001_armature_copy: bpy.types.Object = bpy.data.objects.get('body001.body.armature.001')

        out_file_0 = f'{self.output_dir}/{self._testMethodName}.ex.anm'

        self.activate_object(body001_armature_object)
        pose: bpy.types.Pose = body001_armature_object.pose
        neck: bpy.types.PoseBone = pose.bones.get('Bip01 Neck')
        neck.scale = Vector((1, 10, 20))
        print(neck.scale)

        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_0, is_scale=True)

        self.activate_object(body001_armature_copy)
        bpy.ops.import_anim.import_cm3d2_anm(filepath=out_file_0)

        # Check the loss
        pose: bpy.types.Pose = body001_armature_object.pose
        pose_copy: bpy.types.Pose = body001_armature_copy.pose
        for bone in pose.bones:
            bone: bpy.types.PoseBone
            bone_copy: bpy.types.PoseBone = pose_copy.bones.get(bone.name)
            if bone_copy is None:
                print(f"Could not find bone {bone.name} in copied armature")
                continue
            loc_expected = bone.location
            loc_actual   = bone_copy.location
            rot_expected = bone.rotation_quaternion
            rot_actual   = bone_copy.rotation_quaternion
            scl_expected = bone.scale
            scl_actual   = bone_copy.scale

            loc_diff: Vector = loc_actual - loc_expected
            rot_diff: Quaternion = rot_actual - rot_expected
            scl_diff: Vector = scl_actual - scl_expected

            # TODO : Use a proper epislon-based floating point precision check
            self.assertAlmostEqual(loc_diff.magnitude * 0.01, 0, 1, msg=f"loc of {bone.name} expected {loc_expected}, got {loc_actual}")
            self.assertAlmostEqual(rot_diff.magnitude * 0.01, 0, 1, msg=f"rot of {bone.name} expected {rot_expected}, got {rot_actual}")
            self.assertAlmostEqual(scl_diff.magnitude * 0.01, 0, 1, msg=f"scl of {bone.name} expected {scl_expected}, got {scl_actual}")
