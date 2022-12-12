import sys
from types import ModuleType
from pathlib import Path
from typing import Dict, Tuple

import pdoc
from pdoc import doc, extract, render
from bpydoc import *


import bpy
import rna_info # blender module; must be imported after bpy



def pdoc_bpy(module: ModuleType, out_dir: str | Path = None) -> Dict[str, Module]:
    """
    Render the documentation for all exported bpy operators.
    """
    if not out_dir is None:
        out_dir = Path(out_dir)

    # To find the module's additions, get RNA info, call register, 
    # then get RNA info again, and find what was added
    base_rna_info_list = rna_info.BuildRNAInfo()
    base_rna_info_keys = ( list(base_rna_info_list[0].keys()),  
                           list(base_rna_info_list[1].keys()), 
                           list(base_rna_info_list[2].keys()), 
                           list(base_rna_info_list[3].keys()))
    module.register()
    both_rna_info_list = rna_info.BuildRNAInfo()
    module_rna_info_list = ({}, {}, {}, {})
    for i in range(len(module_rna_info_list)):
        for k, v in both_rna_info_list[i].items():
            if k not in base_rna_info_keys[i]:
                module_rna_info_list[i][k] = v

    # Store where each struct is to easily resolve it later
    struct_modules = { }
    bpy_modules: Dict[ModuleType, set] = { }
    loaded_modules = { }
    bpy_ops_sub_modules = set()

    def _get_sub_module(module_name):
        return loaded_modules.setdefault(f'bpy.ops.{module_name}', getattr(bpy.ops, op_info.module_name))
    
    def _get_parent(child_key) -> Tuple[Tuple[str, str], InfoMemberRNA, ModuleType]:
        parent_key = ('', child_key[0])
        parent = None
        if parent_key in both_rna_info_list[0].keys():
            parent = both_rna_info_list[0][parent_key]
            parent_module = bpy.types
        elif parent_key in both_rna_info_list[2].keys():
            parent = both_rna_info_list[2][parent_key]
            parent_module = _get_sub_module(parent.module_name)
        return parent_key, parent, parent_module

    def _get_bpyclass(parent, parent_module) -> BpyClass:
        for rna_info_member in bpy_modules.setdefault(parent_module, set()):
            if not isinstance(rna_info_member, BpyClass):
                continue
            if rna_info_member.bpy_obj is parent:
                return rna_info_member
        else: # if loop doesn't terminate
            bpyclass = BpyClass(parent_module.__name__, parent.identity)
            bpy_modules[parent_module].add(bpyclass)
            return bpyclass

    def _set_parent_pre(child_key, child_info):
        parent_key, parent, parent_module = _get_parent(child_key)
        if parent is None:
            print(f"Could not find parent for InfoFunctionRNA[{key}] = {func_info}; assuming bpy.types")
            bpy_modules[parent_module].add(child_info)
        elif parent_key not in base_rna_info_keys:
            # It's parent is part of the target module
            # wait until later to add it
            #print(f"Parent '{parent_key}' of child '{child_key}' is part of the target module")
            pass
        else:
            bpyclass = _get_bpyclass(parent, parent_module)
            bpyclass.rna_member_info.add(child_info)

    for struct_info in module_rna_info_list[0].values():
        bpy_modules.setdefault(bpy.types, set()).add(struct_info)
        struct_modules[struct_info.identifier] = bpy.types
    for op_info in module_rna_info_list[2].values():
        sub_module = _get_sub_module(op_info.module_name)
        bpy_modules.setdefault(sub_module, set()).add(op_info)
        bpy_ops_sub_modules.add(sub_module)
        struct_modules[op_info.identifier] = sub_module
    for key, func_info in module_rna_info_list[1].items():
        _set_parent_pre(key, func_info)
    for key, prop_info in module_rna_info_list[3].items():
        _set_parent_pre(key, prop_info)

    all_modules = {}
    for bpy_module, rna_members in bpy_modules.items():
        pdoc_module = BpyModule(bpy_module, rna_members)
        all_modules[bpy_module.__name__] = pdoc_module
        #print(f'all_modules[{bpy_module.__name__}] = {pdoc_module}')
    
    # handle bpy.ops
    bpy_ops_sub_module_docs = [all_modules[sub_module.__name__] for sub_module in bpy_ops_sub_modules]
    all_modules[bpy.ops.__name__] = BpyModule(bpy.ops, bpy_ops_sub_module_docs)

    #for sub_module in bpy_ops_sub_modules:
    #    all_modules.pop(sub_module.__name__)
    
    bpy_ops_sub_module_doc_names = [module_doc.name for module_doc in bpy_ops_sub_module_docs]
    print(bpy_ops_sub_module_doc_names)

    return all_modules


def pdoc_blender_add_on(module: ModuleType, out_dir: Path | str):
    module_dir = Path(f'{module.__file__}/../').resolve()
    #loaded_modules = bpy.utils.modules_from_path(str(module_dir), set())
    #if module not in loaded_modules:
    #    raise RuntimeError(f"module {module.__name__} could not be loaded as a blender add-on")
    #bpy.utils.load_scripts(refresh_scripts=True)

    all_modules: dict[str, doc.Module] = {}

    source_doc = doc.Module(module)
    #all_modules[module.__name__] = source_doc
    
    for module_name in extract.walk_specs([str(module_dir)]):
        print(module_name)
        all_modules[module_name] = doc.Module.from_name(module_name)

    api_docs = pdoc_bpy(module)
    all_modules.update(api_docs.items())    

    out_dir = Path(out_dir)
    for pdoc_module in all_modules.values():
        out = render.html_module(pdoc_module, all_modules)
        if not out_dir:
            return out
        else:
            outfile = out_dir / f"{pdoc_module.fullname.replace('.', '/')}.html"
            outfile.parent.mkdir(parents=True, exist_ok=True)
            outfile.write_bytes(out.encode())
    
    index = render.html_index(all_modules)
    if index:
        (out_dir / "index.html").write_bytes(index.encode())

    search = render.search_index(all_modules)
    if search:
        (out_dir / "search.js").write_bytes(search.encode())


def main():
    modules_path = Path(f'{__file__}/../../').resolve()
    sys.path.append(str(modules_path)) # Make it possible to find "../CM3D2 Converter"
    cm3d2converter = __import__("CM3D2 Converter")
    pdoc_blender_add_on(cm3d2converter, 'docs/build')

if __name__ == '__main__':
    main()