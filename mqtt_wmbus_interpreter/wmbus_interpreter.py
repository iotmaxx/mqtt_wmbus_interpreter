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

