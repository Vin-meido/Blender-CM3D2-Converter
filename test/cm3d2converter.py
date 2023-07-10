try:
    import CM3D2_Converter
    from CM3D2_Converter import *
    __file__ = CM3D2_Converter.__file__
except:
    from pathlib import Path
    import importlib
    import sys
    sys.path.append( str(Path(__file__).parent.parent) )
    cm3d2converter = importlib.import_module('CM3D2 Converter')
    print(f"cm3d2converter = {cm3d2converter}")
    print(f"dir(cm3d2converter) = {dir(cm3d2converter)}")
    __file__ = cm3d2converter.__file__
    __all__ = {}
    for k in dir(cm3d2converter):
        v = getattr(cm3d2converter, k)
        __all__[k] = v
        locals()[k] = v
    #__all__ = cm3d2converter.__all__
