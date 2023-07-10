from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload

#import pythonnet as clr
import clr

managed_path = Path(__file__).parent.parent / 'Managed'
sys.path.append(str(managed_path))
clr.AddReference('CM3D2.Serialization')

from CM3D2.Serialization.Files import *

if TYPE_CHECKING:
    class Anm:
        def __init__(self):
            self.version: int = 1000
            self.tracks: list[Anm.Track] = []
            self.useMuneKey: Anm.MuneKeyUsage | None

        @property
        def signature(self) -> Literal["CM3D2_ANIM"]:
            pass

        class Track:
            def __init__(self):
                self.path: str = ""
                self.channels: list[Anm.Track.Channel] = []

            @property
            def channelId(self) -> Literal[1]:
                pass

            class Channel:
                def __init__(self):
                    self.channelId: int = 2
                    self.keyframes: list[Anm.Track.Channel.Keyframe] = []

                class Keyframe:
                    def __init__(self):
                        self.time: float = 0.0
                        self.value: float = 0.0
                        self.tanIn: float = 0.0
                        self.tanOut: float = 0.0

        class MuneKeyUsage:
            def __init__(self):
                self.left: bool = False
                self.right: bool = False
