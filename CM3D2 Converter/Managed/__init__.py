""" Importing this module will ensure that pythonnet is properly initialized,
    and that assembly references have been added.
"""

import sys as _sys
from pathlib import Path as _Path
from typing import TYPE_CHECKING as _TYPE_CHECKING

_MANAGED_DIR = _Path(__file__).parent.absolute()

import pythonnet as _pythonnet
_pythonnet.set_runtime('netfx')

from pythonnet import unload

if not _TYPE_CHECKING:
    from clr import *
    _sys.path.append(str(_MANAGED_DIR))

if _TYPE_CHECKING:
    def AddReference(dll_name: str):
        """Reference the specified dll"""
        pass

from System.IO import FileLoadException as _FileLoadException
try:
    AddReference('CM3D2.Serialization')
    AddReference('COM3D2.LiveLink')
except _FileLoadException as ex:
    from System.Reflection import Assembly as _Assembly
    _Assembly.UnsafeLoadFrom(str(_MANAGED_DIR / 'CM3D2.Serialization.dll'))
    _Assembly.UnsafeLoadFrom(str(_MANAGED_DIR / 'COM3D2.LiveLink.dll'))
