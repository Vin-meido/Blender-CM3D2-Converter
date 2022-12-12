from __future__ import annotations

import inspect
from inspect import Parameter
import pkgutil
import traceback
import warnings
from collections.abc import Callable
import typing
from typing import Any, Iterable, Set, Tuple, TypeVar, List, TypeAlias
from types import ModuleType

from pdoc._compat import cache, cached_property
from pdoc import doc_ast, extract
from pdoc.doc_types import empty, resolve_annotations
from pdoc.doc import *
from pdoc.doc import _include_fullname_in_traceback, _docstr, _safe_getattr, _children, _PrettySignature

import bpy
from rna_info import InfoStructRNA, InfoFunctionRNA, InfoOperatorRNA, InfoPropertyRNA# blender module; must be imported after bpy

InfoMemberRNA: TypeAlias = InfoFunctionRNA | InfoOperatorRNA | InfoPropertyRNA
InfoCallableRNA = (InfoFunctionRNA, InfoOperatorRNA)


class RnaNamespace():
    def __init__(self, modulename, qualname):
        self.modulename = modulename
        self.qualname = qualname

    @staticmethod
    def object_from_rna_info(rna_member: InfoMemberRNA) -> Tuple[str, object]:
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
        members: dict[str, Doc] = {}
        for name, obj in self._rna_member_objects.items():
            qualname = f"{self.qualname}.{name}".lstrip(".")
            taken_from = self._taken_from(name, obj)
            doc: Doc[Any] = None
            if isinstance(obj, Doc):
                # It's already a doc object so just forward it
                members[obj.name] = obj
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
                members[doc.name] = doc

        return members

    def _taken_from(self, member_name: str, obj: Any) -> tuple[str, str]:
        return (self.modulename, self.qualname)
    
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
        bpy_obj,
        rna_member_info: Iterable[InfoMemberRNA] = []
    ):
        RnaNamespace.__init__(self, modulename, qualname)
        self.bpy_obj = bpy_obj
        self.rna_member_info: Set[InfoMemberRNA] = set(rna_member_info)

    @cached_property
    def _rna_member_objects(self) -> dict[str, Any]:
        members = {}
        for rna_member in self.rna_member_info:
            if isinstance(rna_member, Doc):
                name = rna_member.name
                obj = rna_member
            else:
                name, obj = self.object_from_rna_info(rna_member)
            members[name] = obj
        return members


class RnaStruct(RnaNamespace, Class):
    def __init__(self, modulename, qualname, rna_struct, taken_from):
        RnaNamespace.__init__(self, modulename, qualname)
        Class.__init__(self, modulename, qualname, rna_struct, taken_from)
        self.rna_struct = rna_struct
    
    @cached_property
    def docstring(self) -> str:
        return f'<b>{self.rna_name}</b><br/>{self.rna_struct.description}'

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
        return []
        bases = [self.rna_struct.base]
        return bases


class BpyModule(RnaInfo, Module):
    def __init__(
        self,
        module: types.ModuleType,
        rna_member_info: Iterable[(InfoMemberRNA, Doc)]
    ):
        """
        Creates a documentation object given the actual
        Python module object.
        """
        Module.__init__(self, module)
        RnaInfo.__init__(self, module.__name__, '', module, rna_member_info)
        self.bpy_module = module

    @cached_property
    def is_package(self) -> bool:
        return True

    @cached_property
    def members(self) -> dict[str, Doc]:
        members: dict[str, Doc] = Module.members.func(self)
        for name, doc in self.bpy_members.items():
            members[name] = doc

        return members

    @cached_property
    def submodules(self) -> list[Module]:
        submodules = []
        for doc in self.bpy_members.values():
            if isinstance(doc, (Module, BpyModule)):
                submodules.append(doc)
        return submodules


class BpyClass(RnaStruct):
    def __init__(
        self, modulename: str, qualname: str, cls: T, taken_from: tuple[str, str], 
        rna_member_info: Iterable[InfoMemberRNA] = []
    ):
        RnaStruct.__init__(self, modulename, qualname, cls.bl_rna, taken_from)
        Class.__init__(self, modulename, qualname, cls, taken_from)
    
    
    @cached_property
    def _rna_member_objects(self) -> dict[str, Any]:
        members = {} #super()._rna_member_objects
        
        for key, info in InfoFunctionRNA.global_lookup.items():
            if key[0] == self.rna_struct.identifier:
                name, obj = self.object_from_rna_info(info)
                members[name] = obj
        
        for key, info in InfoPropertyRNA.global_lookup.items():
            if key[0] == self.rna_struct.identifier:
                name, obj = self.object_from_rna_info(info)
                members[name] = obj
        
        return members

    @cached_property
    def members(self) -> dict[str, Doc]:
        members: dict[str, Doc] = {} #Module.members.func(self)
        for name, doc in self.bpy_members.items():
            members[name] = doc

        return members

    @cached_property
    def bases(self) -> list[tuple[str, str, str]]:
        return []
        bases = [self.rna_struct.base]
        return bases


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
        _ = self.signature # For some reason caching this immediately fixes an error


    @cached_property
    def is_classmethod(self) -> bool:
        return False

    @cached_property
    def is_staticmethod(self) -> bool:
        return True

    @cached_property
    def funcdef(self) -> str:
        return "def"

    @cached_property
    def signature(self) -> inspect.Signature:
        """
        The function's signature.

        This usually returns an instance of `_PrettySignature`, a subclass of `inspect.Signature`
        that contains pdoc-specific optimizations. For example, long argument lists are split over multiple lines
        in repr(). Additionally, all types are already resolved.

        If the signature cannot be determined, a placeholder Signature object is returned.
        """
        props = self.rna_struct.properties
        args = []
        for prop in props:
            if (prop.is_hidden):
                continue
            default = _safe_getattr(prop, 'default', empty)
            args.append(Parameter(prop.identifier, Parameter.KEYWORD_ONLY, default=default))
        sig = _PrettySignature(args)
        return sig
    
    @cached_property
    def members(self) -> dict[str, Doc]:
        members: dict[str, Doc] = {}
        for name, doc in self.bpy_members.items():
            members[name] = doc

        return members


class BpyProperty(Variable):
    def __init__(
        self,
        modulename: str,
        qualname: str,
        prop: bpy.types.Property,
        taken_from: tuple[str, str],
    ):
        docstring = prop.description
        annotation = str(prop.type)
        default_value = _safe_getattr(prop, 'default', empty)
        super().__init__(modulename, qualname, 
            taken_from=taken_from, docstring=docstring, annotation=annotation, default_value=default_value)

