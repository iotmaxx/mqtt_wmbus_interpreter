"""
MIT License

Copyright (c) 2013 Cyrill Brunschwiler, 2023 Ralf Glaser

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from .wmbus import WMBusFrame

# setup known keys dictionary by their device id
keys = {
    '\x57\x00\x00\x44': '\xCA\xFE\xBA\xBE\x12\x34\x56\x78\x9A\xBC\xDE\xF0\xCA\xFE\xBA\xBE',
    '\x00\x00\x00\x00': '\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
}

def interpret(telegram):
    dataBytes = bytearray.fromhex(telegram['data'])
    frame = WMBusFrame()
    frame.parse(dataBytes, keys)
    theData = {
        "manufacturer": frame.get_manufacturer_short()[0:3].decode('UTF-8'),
#        "manufacturer": frame.get_manufacturer_short(),
        "serial": frame.getSerial(),
        "data": frame.getValues()
    }
#    print(f"Mnf: {frame.get_manufacturer_short()}")
#    print(f"Dev: {frame.get_device_id()}")
#    print(f"FC: {frame.get_function_code()}")
#    print(f"JSON: {frame.getValues()}")
#    frame.log(2)
    return theData

