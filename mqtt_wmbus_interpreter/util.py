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

import serial 
from array import array

# global variables
debug = 0


def connect_sniffer(port):
	""" Connect to sniffer device on specified port.
	
	Provides means to connect to the serial tty which is commonly created by 
	FTDI based wireless M-Bus sniffer devices that deliver sniffed wM-Bus
	frames as continuous stream at the tty
	"""
	ser = serial.Serial(
		port=port,
		baudrate=9600,
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		bytesize=serial.EIGHTBITS,
		#rtscts=False,
		timeout=30
	)
	
	ser.open()
	ser.isOpen()
	
	return ser

def loadsample(path):
	""" Load sample frame from file specified by path.
	
	The method supports to load captured wireless M-Bus frames from files for 
	any debugging or replay purposes
	"""
	
	f = open(path,'rb')
	a = array('B', f.read())
	
	if debug:
		print ('-- file contents --')
		print (a)
		print ('-- eof --')
		
	return a   
	
def tohex(v, split=' '):
    """ Return value in hex form as a string (for pretty printing purposes).
    
    The function provides a conversion of integers or byte arrays ('B') into 
    their hexadecimal form separated by the splitter string
    """
    myformat = "%0.2X"
    
    if type(v) == array or type(v) == bytearray:
        return split.join(myformat % x for x in v)
    elif type(v) == str:
        temp = bytearray(v)
        return split.join(myformat % x for x in temp)
    elif type(v) ==  int:
        return myformat % v
    else:
        return "tohex(): unsupported type"
