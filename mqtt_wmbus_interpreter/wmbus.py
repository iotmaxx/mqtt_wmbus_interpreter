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

import sys
from . import util

from array import array
from datetime import datetime
from Crypto.Cipher import AES

debug = 1

from .wmbus_data_record import WMBusDataRecordHeader, WMBusDataRecord
from .wmbus_data_header import WMBusShortDataHeader, WMBusLongDataHeader

class WMBusFrame():

    def __init__(self, *args, **kwargs):

        # just holds the most usefull wireless M-Bus frame params
        self.length = None
        self.control = None
        self.manufacturer = None
        self.address = None
        self.control_information = None
        self.header = None
        self.records = []
        self.data = None
        self.data_size = None
        self.key = None
    
    def parse(self, arr, keys=None):
        """ Parses frame contents and initializes object values
        
        The first steps of setting up an WMBusFrame should be the 
        initialization of the class and passing the wM-Bus frame as an array
        to the parse method in order to initialize the object values. 
        
        Optionally, the parse method takes a keys dictionarry which lists
        known keys by their device id. E.g.
        
        keys = {
            '\x57\x00\x00\x44': '\xCA\xFE\xBA\xBE\x12\x34\x56\x78\x9A\xBC\xDE\xF0\xCA\xFE\xBA\xBE',
            '\x00\x00\x00\x00': '\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
        }
        """

        if len(arr)-1 != arr[0]:
            print ("WARNING: frame length field does not match effective frame length! Decoding might be unreliable. Check your input.")
            
            print (f"frame[0]: {arr[0]}")
            print (f"len(frame)-1: {len(arr)-1}")
        
        if (arr is not None and arr[0] >= 11):
            self.length = arr[0]
            self.control = arr[1]
            self.manufacturer = arr[2:4]
            self.address = arr[4:10]
            self.control_information = arr[10]
            self.data = arr[11:]
            
            if (self.is_with_long_tl()):
                self.header = WMBusLongDataHeader()
                self.header.parse(self.data[0:12])
                self.data = self.data[12:]
                
                '''
                Note that according to the standard, the manufacturer and 
                device id from the transport header have precedence over the
                frame information
                '''
                #self.manufacturer = header.manufacturer
                #self.address[0,4] = header.identification
                #self.address[4] = header.version
                #self.address[5] = header.device_type
                
            elif (self.is_with_short_tl()):
                self.header = WMBusShortDataHeader()
                self.header.parse(self.data[0:4])
                self.data = self.data[4:]
                
            self.data_size = len(self.data)
            
            if (keys):
                devid = ''.join(chr(b) for b in self.get_device_id()) 
                self.key = keys.get(devid, None)
            
            # time might come where we should move this into a function
            if (self.header and self.header.get_encryption_mode() == 5):
                
                # data is encrypted. thus, check if a key was specified
                if (self.key):
                    
                    # setup cipher specs, decrypt and strip padding
                    spec = AES.new(self.key, AES.MODE_CBC, "%s" % self.get_iv())
                    self.data = bytearray(spec.decrypt("%s" % self.data))
                   
                    if debug:
                        print (f"dec: {util.tohex(self.data)}")
                    
                    # check whether the first two bytes are 2F
                    if (self.data[0:2] != '\x2F\x2F'):
                        print (util.tohex(self.data))
                        raise Exception("Decryption failed")
            
#            print(f"RGL: self.data: {' '.join(format(x, '02x') for x in self.data)}")
            start=0
            end=len(self.data)
            while self.data[start] == 0x2f:
                start+=1
            while self.data[end-1] == 0x2f:
                end-=1
            self.data = self.data[start:end]
#            print(f"RGL: self.data: {' '.join(format(x, '02x') for x in self.data)}")
#            self.data = bytearray(self.data.lstrip('\x2F').rstrip('\x2F'))

            if debug:
                print (f"cut: {util.tohex(self.data)}")

            while len(self.data) > 0:
                record = WMBusDataRecord()
                self.data = record.parse(self.data)            
                self.records.append(record)
        else:
            print ("(%d) " % arr[0] + util.tohex(arr) )
            raise Exception("Invalid frame length")
            
    def get_manufacturer_short(self):
        """ Returns the three letter manufacturer code
        
        The method converts the two manufacturer bytes from the object
        initialized values and returns the corresponding manufacturer three
        letter code as assigned by the flag association.
        """
        temp = self.manufacturer[1]
        temp = (temp << 8) + self.manufacturer[0]
        
        short = bytearray(4)
        short[0] = ((temp >> 10) & 0x001F) + 64
        short[1] = ((temp >> 5)  & 0x001F) + 64
        short[2] = (temp & 0x001F) + 64
        short[3] = 0;

        return short
        
    def get_device_id(self):
        """ Returns the device id
        
        The method converts the device id byte information (first four bytes
        in little endian) of the address field and returns an array holding 
        the real device id.
        """
        value = array('B')
        
        # reverse device id (use address field to get id)
        #
        # TODO: maybe value = self.address[0:4].reverse() would do
        for i in range(4):
            value.append(self.address[4-(i+1)])
       
        return value        
        
    def getSerial(self):
        ser = self.address[0:4]
        ser .reverse()
        return ''.join(format(x, '02x') for x in ser)
#        return list(self.address[0:4]) #.reverse()

    def get_device_version(self):
        """ Returns the device version
        
        The method returns the device version byte information (5th byte) of
        the device address.
        """
        return self.address[4]
        
    def log(self, verb):
        """ Print a log record for that frame
        
        The log record consist of the following information
        - timestamp
        - device manufacturer, serial, type and version
        - frame direction, purpose
        
        Depending on the verbosity, additional details could be printed
        - frame header info
        - transport header info
        - data records
        
        The log method takes three levels of verbosity
        0: just single line
        1: additionally log frame header and transpor header info
        2: additionally log data records
        """
        line = datetime.now().strftime("%b %d %H:%M:%S") + " "
        line += util.tohex(self.get_manufacturer_short()) + " "
        line += util.tohex(self.get_device_id()) + " "
        line += self.get_function_code() + " "
        
        if self.records:
            line += 'Records: %d' % len(self.records)
            
            if verb >= 1:
                line += '\n--'
                line += "\nCI Detail:\t" + util.tohex(self.control_information) + " (" + self.get_ci_detail() + ", " + self.get_function_code() + ")"
                line += "\nheader:\t\t" + self.header_details()
                
                
                if (self.is_with_long_tl() or self.is_with_short_tl()):
                    line += "\nhas errors:\t%r" % self.header.has_errors()
                    line += "\naccess:\t\t" + self.header.accessibility()
                    
                    if (self.header.configuration):
                        line += "\nconfig word:\t" + util.tohex(self.header.configuration)
                        line += "\nmode:\t\t%d" % self.header.get_encryption_mode() + " (" + self.header.get_encryption_name() + ")"
                        
                        if (self.is_encrypted()):
                            line += "\niv:\t\t" + util.tohex(self.get_iv())
                            
                            if (self.key):
                                line += "\nkey:\t\t" + util.tohex(self.key)
                            else:
                                line += "\nkey:\t\tWARNING no suitable key configured"
                
                line += '\n--'
                
                if verb >= 2:
                    for rec in self.records:
                         val = rec.value.copy()
                         val.reverse()
                        
                         line += '\nDIFs:\t' + util.tohex(rec.header.dif) 
                         line += " (" + rec.header.get_function_field_name() 
                         line += ", " + rec.header.get_data_field_name() + ")"
                         
                         line += '\nVIFs:\t' + util.tohex(rec.header.vif) 
                         line += " (" + rec.header.get_vif_description() + ")"
                         
                         line += '\nValue:\t' + util.tohex(val)
                         line += '\n--'

#                         print(val)
                         
        else:
            line += 'Data: ' + util.tohex(self.data)
        '''
        line += "v%0.3d" % self.get_device_version() + " "
        line += self.get_device_type() + " (" + util.tohex(self.address[5]) + ") "
        '''
        print (line)

    def getValues(self):
        valList = []
        for rec in self.records:
            val = rec.value.copy()
#            val.reverse()
            recData = {
                "type": rec.header.get_function_field_name(),
                "sensor": rec.header.get_vif_description(),
                "value": rec.header.getDataValue(val),
#                "org": ' '.join(format(x, '02x') for x in val)
            }
            valList.append(recData)
        return valList

    def is_without_tl(self):
        """ Returns True if the CI field indicates no transport layer
        """
        if self.control_information in (0x69, 0x70, 0x78, 0x79):
            return True
            
        return False
        
    def is_with_short_tl(self):
        """ Returns True if the CI field indicates short transport layer
        """
        if self.control_information in (0x61, 0x65, 0x6A, 0x6E, 0x74, 0x7A, 0x7B, 0x7D, 0x7F, 0x8A):
            return True
            
        return False
        
    def is_with_long_tl(self):
        """ Returns True if the CI field indicates long transport layer
        """
        if self.control_information in (0x60, 0x64, 0x6B, 0x6F, 0x72, 0x73, 0x75, 0x7C, 0x7E, 0x80, 0x8B):
            return True
            
        return False
    
    def get_ci_detail(self):
        """ Returns speaking text according to prEN 13575-4 for a CI value
        """
        ci = self.control_information
        
        if ci >= 0xA0 and ci <= 0xB7: 
            return 'Manufacturer specific Application Layer'
        else:
            return {
                0x60: 'COSEM Data sent by the Readout device to the meter with long Transport Layer',
                0x61: 'COSEM Data sent by the Readout device to the meter with short Transport Layer',
                0x64: 'Reserved for OBIS-based Data sent by the Readout device to the meter with long Transport Layer',
                0x65: 'Reserved for OBIS-based Data sent by the Readout device to the meter with short Transport Layer',
                0x69: 'EN 13757-3 Application Layer with Format frame and no Transport Layer',
                0x6A: 'EN 13757-3 Application Layer with Format frame and with short Transport Layer',
                0x6B: 'EN 13757-3 Application Layer with Format frame and with long Transport Layer',
                0x6C: 'Clock synchronisation (absolute)',
                0x6D: 'Clock synchronisation (relative)',
                0x6E: 'Application error from device with short Transport Layer',
                0x6F: 'Application error from device with long Transport Layer',
                0x70: 'Application error from device without Transport Layer',
                0x71: 'Reserved for Alarm Report',
                0x72: 'EN 13757-3 Application Layer with long Transport Layer',
                0x73: 'EN 13757-3 Application Layer with Compact frame and long Transport Layer',
                0x74: 'Alarm from device with short Transport Layer',
                0x75: 'Alarm from device with long Transport Layer',
                0x78: 'EN 13757-3 Application Layer without Transport Layer (to be defined)',
                0x79: 'EN 13757-3 Application Layer with Compact frame and no header',
                0x7A: 'EN 13757-3 Application Layer with short Transport Layer',
                0x7B: 'EN 13757-3 Application Layer with Compact frame and short header',
                0x7C: 'COSEM Application Layer with long Transport Layer',
                0x7D: 'COSEM Application Layer with short Transport Layer',
                0x7E: 'Reserved for OBIS-based Application Layer with long Transport Layer',
                0x7F: 'Reserved for OBIS-based Application Layer with short Transport Layer',
                0x80: 'EN 13757-3 Transport Layer (long) from other device to the meter',
                0x81: 'Network Layer data',
                0x82: 'For future use',
                0x83: 'Network Management application',
                0x8A: 'EN 13757-3 Transport Layer (short) from the meter to the other device',
                0x8B: 'EN 13757-3 Transport Layer (long) from the meter to the other device',
                0x8C: 'Extended Link Layer I (2 Byte)',
                0x8D: 'Extended Link Layer II (8 Byte)'
                }.get(ci, 'get_ci_detail(): unknown CI value')
                
    def get_iv(self):
        """ Returns the IV in little endian

        The IV is derived from the manufacturer bytes, the device address and
        the access number from the data header. Note, that None is being 
        returned if the current mode does not specify an IV or the IV for that
        specific mode is not implemented.
        
        Currently implemented IVs are:
        - IV for mode 2 encryption
        - IV for mode 4 encryption
        - IV for mode 5 encryption
        """
        if self.header:
            if self.header.get_encryption_mode() == 2:
                return bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00')
        
            if self.header.get_encryption_mode() == 4:
                return bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
               
            if self.header.get_encryption_mode() == 5:
                '''
                According to prEN 13757-3 the IV for mode 5 is setup as follows
                
                LSB 1   2   3   4   5   6   7   8   9   10  11  12  13  14  MSB
                Man Man ID  ..  ..  ID  Ver Med Acc ..  ..  ..  ..  ..  ..  Acc
                LSB MSB LSB         MSB sio ium 
                '''
                iv = bytearray()
                iv[:2] = self.manufacturer
                iv[2:8] = self.address
                
                for i in range(8,16):
                    iv.append(self.header.access_nr)
                
                return iv
    
        return None
        
    def get_function_code(self):
        """ Return short for function code depending on control info byte
        
        Function codes

        0h SND-NKE To meter     Link reset after communication        
        3h SND-UD  To meter     Send a command (Send User Data)
        4h SND-NR  From meter   Send unsolicited/periodical application data 
                                without request (Send/No Reply) 
        6h SND-IR  From meter   Send manually initiated installation data
        7h ACC-NR  From meter   Send unsolicited/periodical message to provide 
                                the opportunity of access to the meter 
        8h ACC-DMD From meter   Access demand from meter to other device. 
                                This message request an access to the meter 
        Ah REQ-UD1 To meter     Alarm request
        Bh REQ-UD2 To meter     Data request 
        """
        
        code = self.control & 0x0F
        
        return {
            0x0: 'SND-NKE',
            0x3: 'SND-UD',
            0x4: 'SND-NR',
            0x6: 'SND-IR',
            0x7: 'ACC-NR',
            0x8: 'ACC-DMD',
            0xA: 'REQ-UD1',
            0xB: 'REQ-UD2'
            }.get(code, 'get_function_code(): unknown code')
        
    def get_device_type(self):
            
        if (self.address[5] >= 0x40): 
            return 'Reserved'
            
        return {
            0x00: 'Other',
            0x01: 'Oil',
            0x02: 'Electricity',
            0x03: 'Gas',
            0x04: 'Head',
            0x05: 'Steam ',
            0x06: 'Warm water (30-90 °C)',
            0x07: 'Water ',
            0x08: 'Heat cost allocator ',
            0x09: 'Compressed air ',
            0x0A: 'Cooling load meter (Volume measured at return temperature: outlet)',
            0x0B: 'Cooling load meter (Volume measured at flow temperature: inlet)',
            0x0C: 'Heat (Volume measured at flow temperature: inlet)',
            0x0D: 'Heat / Cooling load meter',
            0x0E: 'Bus / System component',
            0x0F: 'Unknown medium',
            0x10: 'Reserved for consumption meter',
            0x11: 'Reserved for consumption meter',
            0x12: 'Reserved for consumption meter',
            0x13: 'Reserved for consumption meter',
            0x14: 'Calorific value',
            0x15: 'Hot water (≥ 90 °C)',
            0x16: 'Cold water',
            0x17: 'Dual register (hot/cold) water meter',
            0x18: 'Pressure',
            0x19: 'A/D Converter',
            0x1A: 'Smoke detector',
            0x1B: 'Room sensor (eg temperature or humidity)',
            0x1C: 'Gas detector',
            0x1D: 'Reserved for sensors',
            0x1F: 'Reserved for sensors',
            0x20: 'Breaker (electricity)',
            0x21: 'Valve (gas or water)',
            0x22: 'Reserved for switching devices',
            0x23: 'Reserved for switching devices',
            0x24: 'Reserved for switching devices',
            0x25: 'Customer unit (display device)',
            0x26: 'Reserved for customer units',
            0x27: 'Reserved for customer units',
            0x28: 'Waste water',
            0x29: 'Garbage',
            0x2A: 'Reserved for Carbon dioxide',
            0x2B: 'Reserved for environmental meter',
            0x2C: 'Reserved for environmental meter',
            0x2D: 'Reserved for environmental meter',
            0x2E: 'Reserved for environmental meter',
            0x2F: 'Reserved for environmental meter',
            0x30: 'Reserved for system devices',
            0x31: 'Reserved for communication controller',
            0x32: 'Reserved for unidirectional repeater',
            0x33: 'Reserved for bidirectional repeater',
            0x34: 'Reserved for system devices',
            0x35: 'Reserved for system devices',
            0x36: 'Radio converter (system side)',
            0x37: 'Radio converter (meter side)',
            0x38: 'Reserved for system devices',
            0x39: 'Reserved for system devices',
            0x3A: 'Reserved for system devices',
            0x3B: 'Reserved for system devices',
            0x3C: 'Reserved for system devices',
            0x3D: 'Reserved for system devices',
            0x3E: 'Reserved for system devices',
            0x3F: 'Reserved for system devices'
            }.get(self.address[5], 'get_device_type(): type unknown')
            
    def header_details(self):
        """ Returns a text indicating what header is being used
        """

        text = ''
        
        if (self.is_without_tl()):
            text = 'w/o header'
            
        if (self.is_with_short_tl()):
            text = 'short header'
            
        if (self.is_with_long_tl()):
            text = 'long header'
            
        return text
        
    def is_encrypted(self):
        """ Returns False if the captured frame signals "No encryption"
        """
        
        if (self.header.configuration[0] & 0x0F != 0):
            return True
        
        return False

 
