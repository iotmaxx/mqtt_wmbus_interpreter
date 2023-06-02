class WMBusShortDataHeader():
    
    def __init__(self, *args, **kwargs):
        # holds the short transport header params as specified in prEN 13757-3
        self.access_nr = None
        self.status = None
        self.configuration = None
        
    def parse(self, arr):
        """ Parses frame contents and initializes object values
        
        Normally, objects of this class are being intantiated while the 
        WMBusFrame.parse() method is being invoked.
        """
        self.access_nr = arr[0]
        self.status  = arr[1]
        self.configuration = arr[2:4]
        
        # swap configuration bytes as these arrive little endian
        swap = self.configuration[0]
        self.configuration[0] = self.configuration[1]
        self.configuration[1] = swap
        
    def get_status_detail(self):
        """
        TODO:
        - The function does not anything yet
        - Return a speaking name for errors flagged in the status byte
        
        Bit Meaning with bit set        Significance with bit not set
        --  --                          --
        2   Power low                   Not power low
        3   Permanent error             No permanent error
        4   Temporary error             No temporary error
        5   Specific to manufacturer    Specific to manufacturer
        6   Specific to manufacturer    Specific to manufacturer
        7   Specific to manufacturer    Specific to manufacturer
        
        Status bit 1 bit 0 Application status
        --
        00 No error
        01 Application busy
        10 Any application error
        11 Abnormal condition / alarm
        """
        pass
        
    def has_errors(self):
        """
        Returns true if the header status byte flags errors and alarms
        """
        if self.status & 0xC0:
            return True
            
        return False
        
    def get_encryption_mode(self):
        """ Returns the mode number as defined in prEN 13575-3
        """
        return self.configuration[0] & 0x0F
        
    def get_encryption_name(self):
        """ Return speaking name for encryption mode (defined in prEN 13575-3)
        
        Note, that OMS Security Report and BSI TRs resp. OMS 4 define further 
        modes currently not covered here.
        
        0 No encryption used
        1 Reserved
        2 DES encryption with CBC; IV is zero (deprecated)
        3 DES encryption with CBC; IV is not zero (deprecated)
        4 AES encryption with CBC; IV is zero
        5 AES encryption with CBC; IV is not zero
        6 Reserved for new encryption
        7 - 15 Reserved
        """
        mode = self.configuration[0] & 0x0F
        
        if mode == 0:
            return "No encryption used"
        
        if mode == 1 or mode >= 6:
            return "Reserved"
        
        return {
            2: "DES encryption with CBC; IV is zero (deprecated)",
            3: "DES encryption with CBC; IV is not zero (deprecated)",
            4: "AES encryption with CBC; IV is zero",
            5: "AES encryption with CBC; IV is not zero"
        }.get(mode)
            
    def accessibility(self):
        """ Provides information on the accessibility of the sending device
        
        0 0 No access - Meter provides no access windows (unidirectional)
        0 1 Temporary no access - Meter would generally allow access
        1 0 Limited access - Meter provides a short access windows only 
            immediately after this transmission (e.g. battery operated meter)
        1 1 Unlimited access – Meter provides unlimited access at least until 
            next transmission (e.g. mains powered devices)
        """
        
        config = self.configuration[0] & 0xC0
        
        if (config == 0x00):
            return 'No access'
        elif (config & 0x40):
            return 'Temporary no access'
        elif (config & 0x80):
            return 'Limited access'
        elif (config & 0xC0):
            return 'Unlimited access' 
            
        return 'accessibility(): unkown ...this should never happen'

class WMBusLongDataHeader(WMBusShortDataHeader):
    
    def __init__(self, *args, **kwargs):
        # holds the long transport header params as specified in prEN 13757-3
        self.identification = None
        self.manufacturer = None
        self.version = None
        self.device_type = None
    
    def parse(self, arr):
        """ Parses frame contents and initializes object values
        
        Normally, objects of this class are being intantiated while the 
        WMBusFrame.parse() method is being invoked. Note, that this method
        also initializes values from its base class.
        """
        self.identification = arr[0:4]
        self.manufacturer = arr[4:6]
        self.version = arr[6]
        self.device_type = arr[7]
        
        WMBusShortDataHeader.parse(self, arr[8:12])
    
        
