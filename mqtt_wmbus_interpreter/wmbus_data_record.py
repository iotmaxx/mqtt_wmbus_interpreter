from . import util
from struct import unpack

def convert_from_bcd(bcd):
    """ Converts a bcd value to a decimal value

    :param value: The value to unpack from bcd
    :returns: The number in decimal form
    """
    place, decimal = 1, 0
    while bcd > 0:
        nibble = bcd & 0xf
        decimal += nibble * place
        bcd >>= 4
        place *= 10
    return decimal


class WMBusDataRecordHeader():
        
    MAX_DIFS_AND_MAX_VIFS = 10
    DATA_TYPE_FIXED = 0
    DATA_TYPE_VARIABLE = 1
    DATA_TYPE_SELECTION_FOR_READOUT = 2
    DATA_TYPE_SPECIAL_FUNCTION = 3
    
    def __init__(self, *args, **kwargs):
        self.dif = bytearray()
        self.vif = bytearray()
    
    def parse(self, arr):
        """ Parses the data head for valid dif/vif structure 
        
        It returns the value part
        """ 
        nr_difs = self.get_difs(arr)
        nr_vifs = self.get_vifs(arr[nr_difs:])
        
        if len(self.dif) > WMBusDataRecordHeader.MAX_DIFS_AND_MAX_VIFS:
            raise Exception("parse(): Nr. of DIFs exceeds specified length")
        if len(self.vif) > WMBusDataRecordHeader.MAX_DIFS_AND_MAX_VIFS:
            raise Exception("parse(): Nr. of VIFs exceeds specified length")
        else:
            var = 0
            
            if (self.get_data_type() == WMBusDataRecordHeader.DATA_TYPE_VARIABLE):
                var = 1
                
            start = nr_difs+nr_vifs+var
            stop = start + self.get_data_len(arr)
            
            return arr[start:stop]
    
    def get_difs(self, arr):
        """ Returns the number DIFs for the provided data
        
        Special functions
        --
        0Fh Start of manufacturer specific data structures to end of user data
        1Fh Same meaning as DIF = 0Fh + More records follow in next telegram
        2Fh Idle filler, following byte = DIF of next record
        3Fh ... 6Fh Reserved
        7Fh Global readout req (all storage nrs, units, tariffs, func. fields)
        """
        cnt = 0
        dif = arr[cnt]
            
        # check whether the DIF signals a special function
        if dif in (0x0F, 0x1F, 0x2F, 0x7F) or dif >= 0x3F and dif <= 0x6F:
            self.dif.append(dif)
            return cnt + 1
            
        # check whether the DIF has an extension (additional DIFs follow)
        while (dif & 0x80) == 0x80:
            self.dif.append(dif)
            cnt += 1
            dif = arr[cnt]
        
        # add final value
        self.dif.append(dif)
                        
        return cnt + 1
        
    def get_vifs(self, arr):
        """ Returns the number of VIFs for the provided data
        """
        cnt = 0
        vif = arr[cnt]
        
        # check whether the VIF has an extension (additional VIFs follow)
        while (vif & 0x80) == 0x80:
            self.vif.append(vif)
            cnt += 1
            vif = arr[cnt]
            
        # add final value
        self.vif.append(vif)
        
        return cnt + 1    
        
    def get_data_type(self):
        """ Returns hints on the data type according to the DIF
        """
        chooser = self.dif[0] & 0x0F
        
        if (chooser == 0x8):
            return self.DATA_TYPE_SELECTION_FOR_READOUT
        elif (chooser == 0xD):
            return self.DATA_TYPE_VARIABLE
        elif (chooser == 0xF):
            return self.DATA_TYPE_SPECIAL_FUNCTION
        else:
            return self.DATA_TYPE_FIXED
        
    def get_data_len(self, arr):
        """ Returns the record value number of bytes 
        
        Note, that for unknown and variable length types, None is being
        returned.
        
        Len     Code Meaning                Code Meaning
        --
        0       0000 No data                1000 Selection for Readout
        8       0001 8 Bit Integer/Binary   1001 2 digit BCD
        16      0010 16 Bit Integer/Binary  1010 4 digit BCD
        24      0011 24 Bit Integer/Binary  1011 6 digit BCD
        32      0100 32 Bit Integer/Binary  1100 8 digit BCD
        32/N    0101 32 Bit Real            1101 variable length
        48      0110 48 Bit Integer/Binary  1110 12 digit BCD
        64      0111 64 Bit Integer/Binary  1111 Special Functions
        """
         
        chooser = self.dif[0] & 0x0F
        
        if chooser == 0xD:
            '''
            the value is variable length and we therefore need to read the
            length of the variable value from the first byte of the actual
            value resp. from the first byte after the record header.
            '''
            return arr[len(self.dif)+len(self.vif)+1]
        else:
            return {
                0x0: 0,
                0x1: 1,
                0x2: 2,
                0x3: 3,
                0x4: 4,
                0x5: 4,
                0x6: 6,
                0x7: 8,
                0x9: 1,
                0xA: 2,
                0xB: 3,
                0xC: 4,
                0xE: 6
            }.get(chooser, -1)

    def get_data_field_name(self):
        """ Returns a speaking name for the DIF data field
        """
        chooser = self.dif[0] & 0x0F
        
        return {
            0x0: 'No data',
            0x1: '8 Bit Integer/Binary',
            0x2: '16 Bit Integer/Binary',
            0x3: '24 Bit Integer/Binary',
            0x4: '32 Bit Integer/Binary',
            0x5: '32 Bit Real',
            0x6: '48 Bit Integer/Binary',
            0x7: '64 Bit Integer/Binary',
            0x8: 'Selection for Readout',
            0x9: '2 digit BCD',
            0xA: '4 digit BCD',
            0xB: '6 digit BCD',
            0xC: '8 digit BCD',
            0xD: 'variable length',
            0xE: '12 digit BCD',
            0xF: 'Special Functions'
        }.get(chooser)
    

    def getDataValue(self, value):
        chooser = self.dif[0] & 0x0F
        if chooser == 0x0:
            return None
        elif chooser == 0x1:
            return value[0]
        elif chooser == 0x2:
            return int.from_bytes(value[0:2],'little',signed=True)
        elif chooser == 0x3:
            return int.from_bytes(value[0:3],'little',signed=True)
        elif chooser == 0x4:
            return int.from_bytes(value[0:4],'little',signed=True)
        elif chooser == 0x5:
            return unpack('<f', value)[0]
        elif chooser == 0x6:
            return int.from_bytes(value[0:6],'little',signed=True)
        elif chooser == 0x7:
            return int.from_bytes(value[0:8],'little',signed=True)
        elif chooser == 0x8:
            return None
        elif chooser == 0x9:
            return convert_from_bcd(value[0])
        elif chooser == 0xA:
            return convert_from_bcd(int.from_bytes(value[0:2],'little',signed=False))
        elif chooser == 0xB:
            return convert_from_bcd(int.from_bytes(value[0:3],'little',signed=False))
        elif chooser == 0xC:
            return convert_from_bcd(int.from_bytes(value[0:4],'little',signed=False))
        elif chooser == 0xD:
            return None
        elif chooser == 0xE:
            return convert_from_bcd(int.from_bytes(value[0:6],'little',signed=False))
        elif chooser == 0xF:
            return None

    def get_function_field_name(self):
        """ Returns a speaking name for the DIF function field
        """
        chooser = self.dif[0] & 0x30
        
        return {
            0x00: 'Instantaneous value',
            0x10: 'Maximum value',
            0x20: 'Minimum value',
            0x30: 'Value during error state'
        }.get(chooser)
        
    def get_vif_description(self):
        """ Return a speaking name for the primary VIF
        
        TODO: Not yet implemented units
        
        PRIMARY
        ---
        E110 1101 b	Date and time (actual or associated with a storage number/function)		data field= 0100b, type F
        E110 1101 b	Extended time point (actual or associated with a storage number/function)	Time to s 	data field= 0011b, type J
        E110 1101 b	Extended date and time point (actual or associated with a storage number/function)	Time and date to sec. 	data field= 0110b, type I
        
        SPECIAL
        ---
        1111 1011	First extension of VIF-codes	True VIF is given in the first VIFE and is coded using (table 29 in 7.5) (128 new VIF-Codes)
        E111 1100	VIF in following string (length in first byte)	Allows user definable VIF ́s (in plain ASCII-String)
        1111 1101	Second extension of VIF-codes	True VIF is given in the first VIFE and is coded using (table 28 in 7.4) (128 new VIF-Codes)
        1110 1111	Reserved for third extension table of VIF-codes	reserved for a future table especially for electricity meters
        E111 1110	Any VIF	Used for readout selection of all VIF ́s (see 6.4)
        E111 1111	Manufacturer specific	VIFE ́s and data of this block are manufacturer specific
        
        MAIN
        ---
        E000 00nn	Credit of 10nn-3 of the nominal local legal currency units	Currency Units
        E000 01nn	Debit of 10nn-3 of the nominal local legal currency units
        E000 1000	Unique telegram identification (previously named “Access Number (transmission count)”)
        E000 1001	Device type
        E000 1010	Manufacturer
        E000 1011	Parameter set identification	Enhanced Identification
        E000 1100	Model / Version
        E000 1101	Hardware version number
        E000 1110	Metrology (firmware) version number
        E000 1111	Other software version number
        E001 0000	Customer location
        E001 0001	Customer
        E001 0010	Access code user
        E001 0011	Access code operator	Improved Selection and other requirements
        E001 0100	Access code system operator
        E001 0101	Access code developer
        E001 0110	Password
        E001 0111	Error flags (binary) (device type specific)
        E001 1000	Error mask
        E001 1001	Reserved
        E001 1010	Digital output (binary)
        E001 1011	Digital Input (binary)
        E001 1100	Baud rate [baud]
        E001 1101	Response delay time [bit-times]
        E001 1110	Retry
        E001 1111	Remote control (device specific e.g. gas valve)
        E010 0000	First storage number for cyclic storage
        E010 0001	Last storage number for cyclic storage
        E010 0010	Size of storage block
        E010 0011	Reserved	Enhanced storage management
        E010 01nn	Storage interval [sec(s) ... day(s)]
        E010 1000	Storage interval month(s)
        E010 1001	Storage interval year(s)
        E010 1010	Operator specific data
        E010 1011	Time point second (0 to 59)
        E010 11nn	Duration since last readout [sec(s) ... day(s)] a
        E011 0000	Start (date/time) of tariff b
        E011 00nn	Duration of tariff (nn=01 ... 11: min to days)
        E011 01nn	Period of tariff [sec(s) to day(s)] a
        E011 1000	Period of tariff months(s)	Enhanced tariff management
        E011 1001	Period of tariff year(s)
        E011 1010	Dimensionless / no VIF
        E011 1011	Data container for wireless M-Bus protocol
        E011 11nn	Period of nominal data transmissions [sec(s) to day(s)]a (e.g. for RF-transmissions)	Installation and start up electrical units
        E100 nnnn	10nnnn-9 Volts
        E101 nnnn	10nnnn-12 A
        E110 0000	Reset counter
        E110 0001	Cumulation counter
        E110 0010	Control signal
        E110 0011	Day of week e
        E110 0100	Week number
        E110 0101	Time point of day change
        E110 0110	State of parameter activation
        E110 0111	Special supplier information
        E110 10pp	Duration since last cumulation [hour(s) ... years(s)]c
        E110 11pp	Operating time battery [hour(s)..years(s)] c
        E111 0000	Date and time of battery change
        E111 0001	RF level units: dBm d
        E111 0010	Day light saving (beginning, ending, deviation) data type K
        E111 0011	Listening window management data type L
        E111 0100	Remaining battery life time (days)
        E111 0101	Number times the meter was stopped
        E111 0110	Data container for manufacture specific protocol
        E111 0111 – E111 1111	Reserved
        
        ALTERNATE EXTENDED VIFE

        E000 000n	Energy 10(n-1) MWh 0.1MWh to 1MWh
        E000 001n	Reactive energy 10(n) kVARh 1 to 10 kVARh
        E000 01nn	Reserved
        E000 100n 	Energy 10(n-1) GJ 0.1GJ to 1GJ
        E000 101n 	Reserved 
        E000 11nn	Energy 10(n-1) MCal 0.1MCal to 100 MCal
        E001 000n	Volume 10(n+2) m3 
        E001 001n	Reserved 
        E001 01nn	Reactive power 10(nn-3) 0.001 kVAR to 1 kVAR
        E001 100n	Mass 10(n+2) t 100 t to 1 000 t
        E001 101n	Relative humidity 10(n-1) % 0.1% to 100%
        E001 1100 – E001 1111	Reserved 
        E010 0000	Volume feet
        E010 0001	Volume 0,1 feet
        E010 0010	Reserved
        E010 0011	Reserved
        E010 0100	Reserved
        E010 0101	Reserved
        E010 0110	Reserved
        E010 0111	Reserved
        E010 100n	Power 10(n-1) 0,1 MW to 1 MW
        E010 1010	Phase U-U (volt. to volt.) 0.1°
        E010 1011	Phase U-I (volt. to current) 0.1°
        E010 11nn	Frequency 10(nn-3) Hz 0.001 Hz to 1 Hz
        E011 000n	Power 10(n-1) 0,1 GJ/h to 1 GJ/h
        E011 0010 – E101 0111	Reserved 
        E101 10nn	Reserved
        E101 11nn	Reserved
        E110 00nn	Reserved
        E110 01nn	Reserved
        E110 1nnn	Reserved
        E111 00nn	Reserved
        E111 01nn	Cold/warm temperature limit 10(nn-3) °C 0,001 °C to 1 °C
        E111 1nnn	Cum. count max. power 10(nnn-3) W 0,001 W to 10 000 W

        COMBINABLE (ORTHOGONAL) VIFE
        ---
        E000 xxxx	Reserved for object actions (master to slave): see clause 9 or for error codes (slave to master): see 8.4
        E001 0000 – E001 1011 Reserved
        E001 1100	Standard conform data content d
        E001 1101	Reserved
        E001 1110	Compact profile with registers e
        E001 1111	Compact profile without registers e
        E010 0000	per second
        E010 0001	per minute
        E010 0010	per hour
        E010 0011	per day
        E010 0100	per week
        E010 0101	per month
        E010 0110	per year
        E010 0111	per revolution / measurement
        E010 100p	increment per input pulse on input channel number p
        E010 101p	increment per output pulse on output channel number p
        E010 1100	per litre
        E010 1101	per m3
        E010 1110	per kg
        E010 1111	per K (Kelvin)
        E011 0000	per kWh
        E011 0001	per GJ
        E011 0010	per kW
        E011 0011	per (K*l) (Kelvin*litre)
        E011 0100	per V (volt)
        E011 0101	per A (ampere)
        E011 0110	multiplied by s
        E011 0111	multiplied by s / V
        E011 1000	multiplied by s / A
        E011 1001	start date(/time) of a, b
        E011 1010	VIF contains uncorrected unit or value at metering conditions instead of converted unit
        E011 1011	accumulation only if positive contributions (forward flow contribution)
        E011 1100	accumulation of abs value only if negative contributions (backward flow)
        E011 1101	reserved for alternate non-metric unit system (see Annex C)
        E011 1110	Value at base conditions c
        E011 1111	OBIS-declaration (data type C follows in case of binary coding)
        E100 u000	U = 1: upper, u = 0: lower limit value
        E100 u001	Number of exceeds of lower u = 0) / upper (U = 1) limit
        E100 uf1b	Date (/time) of: b = 0: begin, b = 1: end of, f = 0: first, f = 1: last, u = 0: lower, u = 1: upper limit exceed
        E101 ufnn	Duration of limit exceed (u, f: as above, nn = duration)
        E110 0fnn 	Duration of a, b (f: as above, nn = duration)
        E110 1u00	Value during lower (u = 0), upper (u = 1) limit exceed
        E110 1001	Leakage values
        E110 1101	Overflow values
        E110 1f1b	Date (/time) of a (f,b: as above)
        E111 0nnn	Multiplicative correction factor: 10nnn-6
        E111 10nn	Additive correction constant: 10nn-3 • unit of VIF (offset)
        E111 1100	Extension of combinable (orthogonal) VIFE-Code
        E111 1101	Multiplicative correction factor for value (not unit): 103
        E111 1110	Future value
        E111 1111	Next VIFE's and data of this block are manufacturer specific


        EXTENSION oF COMBINABLE VIFE TABLE
        ---
        E000 0000	Reserved
        E000 0001	at phase L1
        E000 0010	at phase L2
        E000 0011	at phase L3
        E000 0100	at neutral (N)
        E000 0101	between phase L1 and L2
        E000 0110	between phase L2 and L3
        E000 0111	between phase L3 and L1
        E000 1000 – E000 1111	Reserved
        E001 0000	accumulation of abs. value for both positive and negative contribution (absolute count)
        E001 0001 – E111 1111	Reserved
        
        """
        extension = self.vif[0] & 0x80
        chooser = self.vif[0] & 0x7F
        
        if (extension):
            if chooser == 0x7B:
                return {
                    0x1A: 'RH 10⁻¹ %',
                    0x1B: 'RH %',
                }.get(self.vif[1], '1st ext. VIF not found')
                
            return {
                0xFB: 'First extension of VIF-codes',   # True VIF is given in the first VIFE and is coded using 128 new VIF-Codes (table 29)
                0xFD: 'Second extension of VIF-codes',  # True VIF is given in the first VIFE and is coded using 128 new VIF-Codes (table 28)
                0xEF: 'Reserved extension'              # Reserved for third extension table of VIF-codes for a future table especially for electricity meters
            }.get(self.vif[0], 'VIF not found')
                
        return {
            0x00: 'Energy mWh',
            0x01: 'Energy 10⁻² Wh',
            0x02: 'Energy 10⁻¹ Wh',
            0x03: 'Energy Wh',
            0x04: 'Energy 10¹ Wh',
            0x05: 'Energy 10² Wh',
            0x06: 'Energy kWh',
            0x07: 'Energy 10⁴ Wh',
            
            0x08: 'Energy J',
            0x09: 'Energy 10¹ J',
            0x0A: 'Energy 10² J',
            0x0B: 'Energy kJ',
            0x0C: 'Energy 10⁴ J',
            0x0D: 'Energy 10⁵ J',
            0x0E: 'Energy MJ',
            0x0F: 'Energy 10⁷ J',
            
            0x10: 'Volume cm³',
            0x11: 'Volume 10⁻⁵ m³',
            0x12: 'Volume 10⁻⁴ m³',
            0x13: 'Volume l',
            0x14: 'Volume 10⁻² m³',
            0x15: 'Volume 10⁻¹ m³',
            0x16: 'Volume m³',
            0x17: 'Volume 10¹ m³',
            
            0x18: 'Mass g',
            0x19: 'Mass 10⁻² kg',
            0x1A: 'Mass 10⁻¹ kg',
            0x1B: 'Mass kg',
            0x1C: 'Mass 10¹ kg',
            0x1D: 'Mass 10² kg',
            0x1E: 'Mass t',
            0x1F: 'Mass 10⁴ kg',
            
            0x20: 'On time seconds',
            0x21: 'On time minutes',
            0x22: 'On time hours',
            0x23: 'On time days',
            
            0x24: 'Operating time seconds',
            0x25: 'Operating time minutes',
            0x26: 'Operating time hours',
            0x27: 'Operating time days',
            
            0x28: 'Power mW',
            0x29: 'Power 10⁻² W',
            0x2A: 'Power 10⁻¹ W',
            0x2B: 'Power W',
            0x2C: 'Power 10¹ W',
            0x2D: 'Power 10² W',
            0x2E: 'Power kW',
            0x2F: 'Power 10⁴ W',
            
            0x30: 'Power J/h',
            0x31: 'Power 10¹ J/h',
            0x32: 'Power 10² J/h',
            0x33: 'Power kJ/h',
            0x34: 'Power 10⁴ J/h',
            0x35: 'Power 10⁵ J/h',
            0x36: 'Power MJ/h',
            0x37: 'Power 10⁷ J/h',
            
            0x38: 'Volume flow cm³/h',
            0x39: 'Volume flow 10⁻⁵ m³/h',
            0x3A: 'Volume flow 10⁻⁴ m³/h',
            0x3B: 'Volume flow l/h',
            0x3C: 'Volume flow 10⁻² m³/h',
            0x3D: 'Volume flow 10⁻¹ m³/h',
            0x3E: 'Volume flow m³/h',
            0x3F: 'Volume flow 10¹ m³/h',
            
            0x40: 'Volume flow ext. 10⁻⁷ m³/min',
            0x41: 'Volume flow ext. cm³/min',
            0x42: 'Volume flow ext. 10⁻⁵ m³/min',
            0x43: 'Volume flow ext. 10⁻⁴ m³/min',
            0x44: 'Volume flow ext. l/min',
            0x45: 'Volume flow ext. 10⁻² m³/min',
            0x46: 'Volume flow ext. 10⁻¹ m³/min',
            0x47: 'Volume flow ext. m³/min',
            
            0x48: 'Volume flow ext. mm³/s',
            0x49: 'Volume flow ext. 10⁻⁸ m³/s',
            0x4A: 'Volume flow ext. 10⁻⁷ m³/s',
            0x4B: 'Volume flow ext. cm³/s',
            0x4C: 'Volume flow ext. 10⁻⁵ m³/s',
            0x4D: 'Volume flow ext. 10⁻⁴ m³/s',
            0x4E: 'Volume flow ext. l/s',
            0x4F: 'Volume flow ext. 10⁻² m³/s',
            
            0x50: 'Mass g/h',
            0x51: 'Mass 10⁻² kg/h',
            0x52: 'Mass 10⁻¹ kg/h',
            0x53: 'Mass kg/h',
            0x54: 'Mass 10¹ kg/h',
            0x55: 'Mass 10² kg/h',
            0x56: 'Mass t/h',
            0x57: 'Mass 10⁴ kg/h',
            
            0x58: 'Flow temperature 10⁻³ °C',
            0x59: 'Flow temperature 10⁻² °C',
            0x5A: 'Flow temperature 10⁻¹ °C',
            0x5B: 'Flow temperature °C',
            
            0x5C: 'Return temperature 10⁻³ °C',
            0x5D: 'Return temperature 10⁻² °C',
            0x5E: 'Return temperature 10⁻¹ °C',
            0x5F: 'Return temperature °C',
            
            0x60: 'Temperature difference mK',
            0x61: 'Temperature difference 10⁻² K',
            0x62: 'Temperature difference 10⁻¹ K',
            0x63: 'Temperature difference K',
            
            0x64: 'External temperature 10⁻³ °C',
            0x65: 'External temperature 10⁻² °C',
            0x66: 'External temperature 10⁻¹ °C',
            0x67: 'External temperature °C',
            
            0x68: 'Pressure mbar',
            0x69: 'Pressure 10⁻² bar',
            0x6A: 'Pressure 10⁻1 bar',
            0x6B: 'Pressure bar',
            
            0x6C: 'Date type G',       # actual or associated with a storage number/function
            0x6D: 'Date/time depending on data field 0100b=type F, 0011b=type J, 0110b=type I',
            0x6E: 'Units for H.C.A.',  # dimensionless
            0x6F: 'Reserved',          # for a future third table of VIF-extensions
            
            0x70: 'Averaging duration seconds',
            0x71: 'Averaging duration minutes',
            0x72: 'Averaging duration hours',
            0x73: 'Averaging duration days',
            
            0x74: 'Actuality duration seconds',
            0x75: 'Actuality duration minutes',
            0x76: 'Actuality duration hours',
            0x77: 'Actuality duration days',
            
            0x78: 'Fabrication no',
            0x79: 'Enhanced identification',
            0x80: 'Address',
            
            0x7C: 'VIF in following string (length in first byte)',  # Allows user definable VIF ́s (in plain ASCII-String)
            0x7E: 'Any VIF',                                         # Used for readout selection of all VIF ́s (see 6.4)
            0x7F: 'Manufacturer specific'                            # VIFEs and data of this block are manufacturer specific
        }.get(chooser)
            
class WMBusDataRecord():

    def __init__(self):
        self.header = WMBusDataRecordHeader()

    def parse(self, arr):
        """ Parses the provided bytearray for a first record 
        
        On success the remaining bytes will be returned. There might be 
        further records to be processed in the returned array. If the 
        function fails, it throws an exception.
        """
        
        self.value = self.header.parse(arr)
        
        var = 0
        
        if (self.header.get_data_type() == WMBusDataRecordHeader.DATA_TYPE_VARIABLE):
            var = 1
            
        len_dif = len(self.header.dif)
        len_vif = len(self.header.vif)
        
        len_total = len_dif + len_vif + var + len(self.value)
        
        return arr[len_total:]
