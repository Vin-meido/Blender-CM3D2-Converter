""" Importing this module will ensure that pythonnet is properly initialized,
    and that assembly references have been added.
"""

import sys as _sys
from pathlib import Path as _Path
from typing import TYPE_CHECKING

_MANAGED_DIR = _Path(__file__).parent.absolute()
_LOADED = False

import pythonnet as _pythonnet

def load():
    global _LOADED
    if not _pythonnet._LOADED:
        _pythonnet.set_runtime('netfx')
    _pythonnet.load()
    _LOADED = True
    _add_references()


def unload() -> bool:
    """Returns true if the runtime was successfuly unloaded."""
    global _LOADED
    if not _LOADED:
        return True
    try:
        _pythonnet.unload()
        _LOADED = False
    except RuntimeError:
        return False
    return True

def reload():
    """Reload the runtime and managed assemblies"""
    import importlib
    if _LOADED:
        unload()
    importlib.reload(_pythonnet)
    load()

def _add_references():
    if TYPE_CHECKING:
        class clr():
            @staticmethod
            def AddReference(dll_name: str):
                """Reference the specified dll"""
    else:
        import clr
    from System.IO import FileLoadException
    from System.Reflection import Assembly
    
    _sys.path.append(str(_MANAGED_DIR))
    
    try:
        clr.AddReference('CM3D2.Serialization')
        clr.AddReference('COM3D2.LiveLink')
    except FileLoadException as ex:
        Assembly.UnsafeLoadFrom(str(_MANAGED_DIR / 'CM3D2.Serialization.dll'))
        Assembly.UnsafeLoadFrom(str(_MANAGED_DIR / 'COM3D2.LiveLink.dll'))
