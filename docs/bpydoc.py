from __future__ import annotations
from ctypes import pointer
from enum import Enum

import inspect
from inspect import Parameter
import pkgutil
import traceback
import warnings
from collections.abc import Callable
import typing
from typing import Any, Iterable, Tuple, Type, TypeVar, TypeAlias
from types import ModuleType
from weakref import ReferenceType

from pdoc._compat import cache, cached_property
from pdoc import doc_ast, extract
from pdoc.doc_types import empty, resolve_annotations
from pdoc.doc import *
from pdoc.doc import _include_fullname_in_traceback, _children, _docstr, _decorators, _safe_getattr, _PrettySignature

import bpy
from rna_info import InfoStructRNA, InfoFunctionRNA, InfoOperatorRNA, InfoPropertyRNA # blender module; must be imported after bpy

InfoMemberRNA: TypeAlias = InfoFunctionRNA | InfoOperatorRNA | InfoPropertyRNA
InfoNamespaceRNA: TypeAlias = InfoStructRNA | InfoOperatorRNA
InfoCallableRNA = (InfoFunctionRNA, InfoOperatorRNA)


class RnaNamespace(Namespace[T], metaclass=ABCMeta):
    def __init__(self, modulename, qualname):
        self.modulename = modulename
        self.qualname = qualname

    @staticmethod
    def _object_from_rna_info(rna_member: InfoMemberRNA) -> Tuple[str, object]:
        name = rna_member.identifier
        obj = rna_member
        if isinstance(rna_member, InfoStructRNA):
            obj = rna_member.py_class
        if isinstance(rna_member, InfoOperatorRNA):
            name = rna_member.func_name
            obj = getattr(getattr(bpy.ops, rna_member.module_name), name)
        if isinstance(rna_member, InfoPropertyRNA):
            d = {}
            for k, v in InfoPropertyRNA.global_lookup:
                if v == rna_member:
                    name = f'{k[0]}.{k[1]}' 
                    break
            obj = rna_member.bl_prop
        return name, obj

    @abstractmethod
    @cached_property
    def _rna_member_objects(self) -> dict[str, Any]:
        return {}
    
    @cached_property
    def bpy_members(self) -> dict[str, Doc]:
        doc_members: dict[str, Doc] = {}
        bpy_members: dict[str, Doc] = {}
        for name, obj in self._rna_member_objects.items():
            qualname = f"{self.qualname}.{name}".lstrip(".")
            taken_from = self._taken_from(name, obj)
            doc: Doc[Any] = None
            if isinstance(obj, Doc):
                # It's already a doc object so just forward it
                doc_members[obj.name] = obj
            elif isinstance(obj, bpy.ops._BPyOpsSubModOp):
                doc = BpyFunction(self.modulename, qualname, obj, taken_from)
            elif isinstance(obj, (bpy.types.Property)):
                doc = BpyProperty(self.modulename, qualname, obj, taken_from)
            elif (
                inspect.isclass(obj)
                and obj is not empty
                and not isinstance(obj, GenericAlias)
                and obj.__qualname__.rpartition(".")[2] == qualname.rpartition(".")[2]
            ):
                doc = BpyClass(self.modulename, qualname, obj, taken_from)
                
            if not doc is None:
                bpy_members[doc.name] = doc

        sorted_doc_members = dict(sorted(doc_members.items()))
        sorted_bpy_members = dict(sorted(bpy_members.items()))
        return sorted_doc_members | sorted_bpy_members

    def _taken_from(self, member_name: str, obj: Any) -> tuple[str, str]:
        modulename = self.modulename
        qualname = self.qualname
        if isinstance(obj, (bpy.types.Property)):
            if hasattr(self, 'obj'):
                modulename = self.obj.__module__
                if hasattr(self.obj, '__qualname__'):
                    qualname = self.obj.__qualname__
            if hasattr(self, 'rna_struct'):
                struct_info = InfoStructRNA.global_lookup.get(('', self.rna_struct.identifier), None)
                if struct_info is not None:
                    modulename = struct_info.module_name
                    qualname = struct_info.identifier
        elif not obj is None:
            modulename = obj.__module__
            if hasattr(obj, '__qualname__'):
                qualname = obj.__qualname__
            elif hasattr(obj, '__name__'):
                qualname = obj.__name__
        return (modulename, qualname)
    
    @abstractmethod
    def members(self) -> dict[str, Doc]:
        pass
    
    @cached_property
    def own_members(self) -> list[Doc]:
        return list(self.members.values())


class RnaInfo(RnaNamespace):
    def __init__(
        self,
        modulename,
        qualname,
        rna_member_info: Iterable[InfoMemberRNA] = []
    ):
        RnaNamespace.__init__(self, modulename, qualname)
        self.rna_member_info: set[InfoMemberRNA] = set(rna_member_info)

    @cached_property
    def _rna_member_objects(self, debugprint=False) -> dict[str, Any]:
        members = {}
        for rna_member in self.rna_member_info:
            if isinstance(rna_member, Doc):
                if debugprint:
                    print(f"Got doc {rna_member}")
                name = rna_member.name
                obj = rna_member
            else:
                name, obj = self._object_from_rna_info(rna_member)
            members[name] = obj
        return members


class RnaStruct(RnaNamespace):
    def __init__(self, modulename, qualname, rna_struct, taken_from):
        RnaNamespace.__init__(self, modulename, qualname)
        self.rna_struct = rna_struct
    
    @cached_property
    def docstring(self) -> str:
        return f'<h5>{self.rna_name}</h5>{self.rna_struct.description}'

    @cached_property
    def rna_name(self) -> str:
        return self.rna_struct.name

    @cached_property
    def _rna_member_objects(self) -> dict[str, Any]:
        members = {}

        for name, prop in self.rna_struct.properties.items():
            if (name == 'rna_type'): 
                continue
            members[name] = prop
        
        for name, func in self.rna_struct.functions.items():
            members[name] = prop
        
        return members

    @cached_property
    def bases(self) -> list[tuple[str, str, str]]:
        base_rna_struct = self.rna_struct.base
        base_rna_info = InfoStructRNA.global_lookup.get(('', base_rna_struct.identifier), None)
        if not base_rna_info is None:
            return [(base_rna_info.module_name, base_rna_info.identifier, f'{base_rna_info.module_name}.{base_rna_info.identifier}')]
        else:
            return []



class BpyNamespace(RnaInfo, Namespace[None]):
    kind = "module"

    def __init__(
        self,
        namespace_name: str,
        rna_member_info: Iterable[(InfoMemberRNA, Doc)]
    ):
        RnaInfo.__init__(self, namespace_name, '', rna_member_info)
        Doc.__init__(self, namespace_name, '', None, (namespace_name, ''))

    @cache
    @_include_fullname_in_traceback
    def __repr__(self):
        return f"<namespace {self.fullname}{_docstr(self)}{_children(self)}>"

    @cached_property
    def members(self) -> dict[str, Doc]:
        return self.bpy_members

    #@cached_property
    #def own_members(self) -> list[Doc]:
    #    return self.members.values()

    @cached_property
    def is_package(self) -> bool:
        return True

    @cached_property
    def submodules(self) -> list[Module]:
        return [x for x in self.members.values() if x.kind == 'module'  ]

    @cached_property
    def variables(self) -> list[Variable]:
        return [x for x in self.members.values() if x.kind == 'variable']

    @cached_property
    def classes(self) -> list[Class]:
        return [x for x in self.members.values() if x.kind == 'class'   ]
    
    @cached_property
    def functions(self) -> list[Function]:
        return [x for x in self.members.values() if x.kind == 'function']


class BpyModule(BpyNamespace, Module):
    def __init__(
        self,
        module: types.ModuleType,
        rna_member_info: Iterable[(InfoMemberRNA, Doc)]
    ):
        BpyNamespace.__init__(self, module.__name__, rna_member_info)
        Module.__init__(self, module)
        self.bpy_module = module

    @cached_property
    def members(self) -> dict[str, Doc]:
        members: dict[str, Doc] = {}#Module.members.func(self)
        members.update(self.bpy_members)
        return members

    @cached_property
    def _var_docstrings(self) -> dict[str, str]:
        return {}
    
    @cached_property
    def _var_annotations(self) -> dict[str, Any]:
        return {} 


class BpyClass(RnaStruct, Class):
    def __init__(
        self, modulename: str, qualname: str, cls: type, taken_from: tuple[str, str], 
        rna_member_info: Iterable[InfoMemberRNA] = [],
        auto_get_members: bool = True
    ):
        RnaStruct.__init__(self, modulename, qualname, cls.bl_rna, taken_from)
        Class.__init__(self, modulename, qualname, cls, taken_from)
        self.auto_get_members = auto_get_members
    
    
    @cached_property
    def _rna_member_objects(self) -> dict[str, Any]:
        members = {} #super()._rna_member_objects
        
        for key, info in InfoFunctionRNA.global_lookup.items():
            if key[0] == self.rna_struct.identifier:
                name, obj = self._object_from_rna_info(info)
                members[name] = obj
        
        for key, info in InfoPropertyRNA.global_lookup.items():
            if key[0] == self.rna_struct.identifier:
                name, obj = self._object_from_rna_info(info)
                members[name] = obj
        
        return members

    @cached_property
    def members(self) -> dict[str, Doc]:
        members: dict[str, Doc] = {} #Module.members.func(self)
        members.update(self.bpy_members)
        return members


class BpyParent(RnaInfo, Class):
    """
    This class is used exclusivly for showing properties and functions
    that were added to already existing classes
    """
    def __init__(
        self, bpy_module: ModuleType, rna_struct: InfoNamespaceRNA, taken_from: tuple[str, str] = None, 
        rna_member_info: Iterable[InfoMemberRNA] = [],
        ignore_rna_info_keys: Tuple[Iterable[InfoStructRNA], Iterable[InfoFunctionRNA], Iterable[InfoOperatorRNA], Iterable[InfoPropertyRNA]] = ([],[],[],[])
    ):
        self.rna_struct = rna_struct
        self.ignore_rna_info_keys = ignore_rna_info_keys
        modulename = bpy_module.__name__
        qualname = rna_struct.identifier
        obj = _safe_getattr(modulename, qualname, bpy.types.bpy_struct)
        if taken_from is None:
            taken_from = (modulename, '')
        Class.__init__(self, modulename, qualname, obj, taken_from)
        RnaInfo.__init__(self, modulename, qualname, rna_member_info)

    @cached_property
    def members(self) -> dict[str, Doc]:
        return self.bpy_members

    @cached_property
    def own_members(self) -> list[Doc]:
        return list(self.members.values())

    @cached_property
    def bases(self) -> list[tuple[str, str, str]]:
        return []

    @cached_property
    def _rna_member_objects(self) -> dict[str, Any]:
        members = RnaInfo._rna_member_objects.func(self)
        
        for key, info in InfoFunctionRNA.global_lookup.items():
            if key in self.ignore_rna_info_keys[1]:
                continue
            if key[0] == self.rna_struct.identifier:
                name, obj = self._object_from_rna_info(info)
                members[name] = obj
        
        for key, info in InfoPropertyRNA.global_lookup.items():
            if key in self.ignore_rna_info_keys[3]:
                continue
            if key[0] == self.rna_struct.identifier:
                name, obj = self._object_from_rna_info(info)
                members[name] = obj
        
        return members


class BpyFunction(RnaStruct, Function):
    kind = 'function'
    def __init__(
        self,
        modulename: str,
        qualname: str,
        func: WrappedFunction,
        taken_from: tuple[str, str],
    ):
        RnaStruct.__init__(self, modulename, qualname, func.get_rna_type(), taken_from)
        Function.__init__(self, modulename, qualname, func, taken_from)

    
    @cached_property
    def docstring(self) -> str:
        docstring = RnaStruct.docstring.func(self)
        props = self.rna_struct.properties
        args = []
        for prop in props:
            if prop.is_hidden:
                continue
            prop_qualname = f'{self.fullname}.{prop.identifier}'
            prop_doc = BpyProperty(self.modulename, prop_qualname, prop, self._taken_from(prop.identifier, prop))
            default = _safe_getattr(prop, 'default', empty)
            docstring += '<br/>'
            docstring += '<div class="classattr">'
            docstring +=     '<div class="attr variable">'
            docstring +=         f'<span class="name">{prop_doc.name}</span>'
            docstring +=         f'<span class="annotation">{prop_doc.annotation_str}</span>'
            docstring +=         f'<span class="default">{prop_doc.default_value_str}</span>'
            docstring +=     '</div>'
            docstring +=     f'{prop_doc.function_docstring}'
            docstring += '</div>'

        return docstring

    @cached_property
    def is_classmethod(self) -> bool:
        return False

    @cached_property
    def is_staticmethod(self) -> bool:
        return True

    @cached_property
    def signature(self) -> inspect.Signature:
        props = self.rna_struct.properties
        args = []
        for prop in props:
            if (prop.is_hidden):
                continue
            default = empty #_safe_getattr(prop, 'default', empty)
            args.append(Parameter(prop.identifier, Parameter.KEYWORD_ONLY, default=default))
        sig = _PrettySignature(args)
        return sig
    
    @cached_property
    def members(self) -> dict[str, Doc]:
        return self.bpy_members


class BpyProperty(Variable):
    def __init__(
        self,
        modulename: str,
        qualname: str,
        prop: bpy.types.Property,
        taken_from: tuple[str, str],
        is_classvar: bool = True
    ):
        self.bpy_prop = prop
        if (prop.is_hidden):
            docstring = prop.description
        else:
            docstring = f'<h5>{self.rna_name}</h5>{self.rna_description}'
        annotation = self._get_type(prop, taken_from)
        default_value = _safe_getattr(prop, 'default', empty)
        super().__init__(modulename, qualname, 
            taken_from=taken_from, docstring=docstring, annotation=annotation, default_value=default_value)

    @cached_property
    def function_docstring(self) -> type:
        if not self.bpy_prop.is_hidden:
            docstring = f'<h5>{self.rna_name}</h5> {self.rna_description}'
        elif self.bpy_prop.description:
            docstring = f'<h5>{self.rna_name} <i>(hidden)</i></h5> {self.rna_description}'
        else:
            docstring = ''
        return docstring

    @cached_property
    def rna_name(self) -> type:
        return self.bpy_prop.name

    @cached_property
    def rna_description(self) -> type:
        return self.bpy_prop.description

    @staticmethod
    def _get_type(prop: bpy.types.Property, taken_from) -> type:
        typedict = {
            'BOOLEAN'    : bool,
            'INT'        : int,
            'FLOAT'      : float,
            'STRING'     : str,
            #'ENUM'       : Enum,
            #'POINTER'    : ReferenceType[T],
            #'COLLECTION' : dict[str, T],
        }
        if prop.type in typedict:
            return typedict[prop.type]
        elif prop.type == 'ENUM':
            return BpyProperty._get_enum_type(prop, taken_from)
        
        #elif prop.type in ('POINTER', 'COLLECTION'):
        struct_info = InfoStructRNA.global_lookup[('', prop.fixed_type.identifier)]
        if prop.type == 'POINTER':
            return struct_info.py_class
        elif prop.type == 'COLLECTION':
            return dict[str, struct_info.py_class]

    @staticmethod
    def _get_enum_type(prop, taken_from):
            prop_enum_items: dict[str, Any] = {}
            for enum_item in prop.enum_items_static.values():
                prop_enum_items[enum_item.identifier] = enum_item.value
            prop_enum: type = type(f'{prop.identifier}_enum', tuple(enum.Enum), prop_enum_items)
            prop_enum.__module__ = taken_from[0]
            prop_enum.__qualname__ = f'{taken_from[1]}.{prop_enum.__name__}'
            return prop_enum

        
