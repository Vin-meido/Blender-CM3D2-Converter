""" Importing this module will ensure that pythonnet is properly initialized,
    and that assembly references have been added.
"""

import sys as _sys
from pathlib import Path as _Path
from typing import TYPE_CHECKING as _TYPE_CHECKING

_MANAGED_DIR = _Path(__file__).parent

import pythonnet as _pythonnet
_pythonnet.set_runtime('netfx', domain='CM3D2Converter', config_file=str(_MANAGED_DIR / 'runtimeconfig.json'))

from clr import *
_sys.path.append(str(_MANAGED_DIR))

if _TYPE_CHECKING:
    def AddReference(dll_name: str):
        """Reference the specified dll"""
        pass
    
AddReference('CM3D2.Serialization')
AddReference('COM3D2.LiveLink')
