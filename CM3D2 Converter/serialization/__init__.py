import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload

#import pythonnet as clr
import clr

managed_path = Path(__file__).parent.parent / 'Managed'
sys.path.append(str(managed_path))
clr.AddReference('CM3D2.Serialization')

from CM3D2.Serialization import *

from . import files

if TYPE_CHECKING:
    class Stream:
        pass
    
    class MemoryStream(Stream):
        pass
    
    class CM3D2Serializer:
        def __init__(self):
            self.SurrogateSelector = None
            self.Binder = None
            self.Context = None
        
        def Serialize(self, serializationStream: Stream, obj):
            pass
        
        def Deserialize(self, serializationStream: Stream, obj = None):
            pass
else:
    from System.IO import Stream, MemoryStream



