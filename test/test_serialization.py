from unittest import TestCase
from cm3d2converter import serialization

class TestCM3D2Serialization(TestCase):
    
    def test_serializer(self):
        serializer = serialization.CM3D2Serializer()
        stream = serialization.MemoryStream()
        anm = serialization.files.Anm()
        serializer.Serialize(stream, anm)
        string = ""
        for byte in stream.GetBuffer():
            byte: int
            string += hex(byte)[2:] + " "
        print(string)