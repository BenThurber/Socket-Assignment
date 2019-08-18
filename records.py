"""A module containing FileRequest and FileResponse which are 
subclasses of Record, which is a subclasses of Packet 
(as defined in packet.py).  

FileRequest and FileResponse build packets (bytearrays) in the 
arrangement specific to each type, and in network byte order.  
Each contain an OrderedDict that defines the format of their 
header.

FileRequest creates an explicit bytearray of Header + FileName 
which can then be sent over the network.

FileResponse can also create an explicit bytearray of 
Header + FileData, or can return Header + FileData in 
blocks of BLOCK_SIZE.  See FileResponse.read_byte_block()

Each class also has static methods that accept a bytearray 
(recieved over the network) convert it host_byte_order, verify 
that it has a valid header, and read values from the header.

The following is the inheritance tree.

          Packet
            |
            V
          Record
          |    |
          V    V
FileRequest    FileResponse

"""

from collections import OrderedDict
import socket
from packet import Packet
import math
import os

BYTE_LEN = 8
BLOCK_SIZE = 4096
ENCODING_TYPE = "UTF-8"

FILE_REQUEST_MAGIC_NO = 0x497E
FILE_REQUEST_TYPE = 1
MAX_FILENAME_LEN = 1024

FILE_RESPONSE_MAGIC_NO = 0x497E
FILE_RESPONSE_TYPE = 2



class Record(Packet):
    """A class between Packet and FileRequest, FileResponse 
    that adds the header and payload to the internal 
    bytearray (via append in Packet class)."""
    
    
    def __init__(self, header_dict, payload_bytes):
        payload_bit_len = len(payload_bytes) * BYTE_LEN
        packet_bit_len = sum(bit_len for bit_len, _ in header_dict.values()) \
            + payload_bit_len
        super().__init__(packet_bit_len)  # Call constructor of Packet
        self._append_header_dictionary(header_dict)
        self._append_payload(payload_bytes)
    
    def _append_header_dictionary(self, dictionary, in_network_order=True):
        """Helper function that takes an OrderedDict of values 
        (bit_len, value).  Adds each value to the internal 
        bytearray in order.  If in_network_order then 
        converts 16-bit and 32-bit integers to network 
        byte order."""
        for bit_len, value in dictionary.values():
            
            if in_network_order:
                value = host_to_network(bit_len, value)
            
            self.append(value, bit_len)
    
    def _append_payload(self, payload_bytearray):
        """Takes each byte from payload_bytearray and adds 
        it to the internal bytearray."""
        for byte in payload_bytearray:
            self.append(byte, BYTE_LEN)
    
    @staticmethod
    def header_to_host_byte_ord(packet_bytearray, header_dict):
        """Takes a bytearray and a header_dict.  Assumes the 
        begining of packet_bytearray is a header in network 
        byte order.  Returns a bytearray representing a 
        header in host order."""
        header_len = sum(bit_len for bit_len, _ in header_dict.values())
        header_len_bytes = math.ceil(header_len / BYTE_LEN)
        
        pkt_net = Packet(header_len, packet_bytearray[:header_len_bytes])
        pkt_host = Packet(header_len)
        
        l_bit = 0
        r_bit = 0
        for bit_len, _ in header_dict.values():
            r_bit += bit_len
            
            value = pkt_net.get_from_bits(l_bit, r_bit)
            value = network_to_host(bit_len, value)
            pkt_host.append(value, bit_len)
            
            l_bit = r_bit + 1
        
        return pkt_host.get_bytearray()
    


class FileRequest(Record):
    '''An object that creates a bytearray representing a 
    FileRequest.  Includes static methods for checking 
    the validity of a recieved FileRequest, and extracting 
    relevent fields.  The payload is of size FilenameLen bytes.
    includes a static OrderedDict of the header with structure:
    "FieldName" : [BitLen, Value] 
    (Value is None for dynamic fields)
    
    By length in bits, a FileRequest header has the following 
    fields:
    "MagicNo", 16
    "Type", 8
    "FilenameLen", 16
    ""
    '''
    
    HEADER_DICT = OrderedDict((
                ("MagicNo", [16, FILE_REQUEST_MAGIC_NO]), 
                ("Type", [8, FILE_REQUEST_TYPE]), 
                ("FilenameLen", [16, None]),
            ))    
    
    def __init__(self, file_name):
        """Takes a filename string."""        
        file_name_bytes = file_name.encode(ENCODING_TYPE)
        
        self.HEADER_DICT["FilenameLen"][-1] = len(file_name_bytes)
        
        super().__init__(self.HEADER_DICT, file_name_bytes)
        
    
    @staticmethod
    def header_to_host_byte_ord(packet_bytearray):
        """Takes a bytearray.  Assumes the begining of 
        packet_bytearray is a header in network byte order.  
        Returns a bytearray representing a header in 
        host order."""
        return Record.header_to_host_byte_ord(
            packet_bytearray, FileRequest.HEADER_DICT
        )
    
    
    @staticmethod
    def get_filenameLen_from_header(packet_bytearray):
        """Takes a bytearray representing a FileRequest 
        header.  Extracts the filenameLen."""
        pkt = Packet(len(packet_bytearray)*BYTE_LEN, packet_bytearray)
        try:
            MagicNo_len = FileRequest.HEADER_DICT["MagicNo"][0]
            Type_len = FileRequest.HEADER_DICT["Type"][0]
            FilenameLen_len = FileRequest.HEADER_DICT["FilenameLen"][0]
            FilenameLen = pkt.get_from_bits(
                1+MagicNo_len+Type_len, MagicNo_len+Type_len+FilenameLen_len
            )
            return FilenameLen
        except IndexError:
            raise ValueError("Invalid FileRequest header")
    
    
    @staticmethod
    def is_valid_header(packet_bytearray):
        """Takes a bytearray is checks if it is a valid FileRequest 
        header.  For the method to return True: 
        MagicNo == 0x497E, 
        Type == 1, 
        1 <= FilenameLen <= 1,024
        """
        is_valid = True
        pkt = Packet(len(packet_bytearray)*BYTE_LEN, packet_bytearray)
        
        MagicNo_len = FileRequest.HEADER_DICT["MagicNo"][0]
        Type_len = FileRequest.HEADER_DICT["Type"][0]
        FilenameLen_len = FileRequest.HEADER_DICT["FilenameLen"][0]
        
        MagicNo = pkt.get_from_bits(0, MagicNo_len)
        if MagicNo != FILE_REQUEST_MAGIC_NO:
            is_valid = False
        
        Type = pkt.get_from_bits(1+MagicNo_len, MagicNo_len+Type_len)
        if Type != FILE_REQUEST_TYPE:
            is_valid = False
        
        FilenameLen = pkt.get_from_bits(
            1+MagicNo_len+Type_len, MagicNo_len+Type_len+FilenameLen_len
        )
        if not (1 <= FilenameLen <= MAX_FILENAME_LEN):
            is_valid = False
        
        return is_valid
    
    
    @staticmethod
    def header_bit_len():
        """Returns the len of the header in bits."""
        try:
            return sum(
                bit_len for bit_len, _ in FileRequest.HEADER_DICT.values()
            )
        except NameError:
            return 0
    
    @staticmethod
    def header_byte_len():
        """Returns the len of the header in bits."""
        return math.ceil(FileRequest.header_bit_len() / BYTE_LEN)    


class FileResponse(Record):
    '''An object that creates a bytearray representing a 
    FileResponse.  Includes static methods for checking 
    the validity of a recieved FileResponse, and extracting 
    relevent fields.  The payload is of size DataLen bytes.  
    Includes a static OrderedDict of the header with structure: 
    "FieldName" : [BitLen, Value] 
    (Value is None for dynamic fields)
    
    By length in bits, a FileRequest header has the following 
    fields:
    "MagicNo", 16
    "Type", 8
    "StatusCode", 8
    "DataLen", 32
    ""
    
    FileResponse is initialized with a file_name and a status 
    code.  Unlike FileRequest, FileResponse does not read 
    the payload into memory.  If .get_bytearray() is called, 
    the whole file is read from file_name and the header and 
    file are returned as a bytearray.  The method 
    .read_byte_block() is a generator that opens a file handle 
    on file_name and returns an amount of bytes equal to 
    BLOCK_SIZE.  First returns header + a part of the file as a 
    bytearray, then returns an amount of the file equal to 
    BLOCK_SIZE on each following itteration.  When the whole 
    file is transfered, the file handle is closed.
    '''
    
    HEADER_DICT = OrderedDict((
            ("MagicNo", [16, FILE_RESPONSE_MAGIC_NO]), 
            ("Type", [8, FILE_RESPONSE_TYPE]), 
            ("StatusCode", [8, None]),
            ("DataLen", [32, None]),
        ))
    
    
    def __init__(self, file_name, status_code):
        """Takes a bytearray that containing a file, and a 
        integer status_code.  If status_code == 0 then 
        no payload is written to the packet."""
        self.file_name = file_name
        self.bytes_read = 0
        self.HEADER_DICT["StatusCode"][-1] = status_code
        try:
            self.HEADER_DICT["DataLen"][-1] = os.path.getsize(file_name)
        except FileNotFoundError:
            self.HEADER_DICT["DataLen"][-1] = 0
        
        super().__init__(self.HEADER_DICT, bytearray())
    
    
    @staticmethod
    def header_to_host_byte_ord(packet_bytearray):
        """Takes a bytearray.  Assumes the begining of 
        packet_bytearray is a header in network byte order.  
        Returns a bytearray representing a header in 
        host order."""
        return Record.header_to_host_byte_ord(
            packet_bytearray, FileResponse.HEADER_DICT
        )
    
    
    @staticmethod
    def get_status_DataLen(packet_bytearray):
        """Takes a bytearray representing a FileRequest 
        header.  Returns (StatusCode, DataLen)."""
        pkt = Packet(len(packet_bytearray)*BYTE_LEN, packet_bytearray)
        try:
            MagicNo_len = FileResponse.HEADER_DICT["MagicNo"][0]
            Type_len = FileResponse.HEADER_DICT["Type"][0]
            StatusCode_len = FileResponse.HEADER_DICT["StatusCode"][0]
            DataLen_len = FileResponse.HEADER_DICT["DataLen"][0]
            StatusCode = pkt.get_from_bits(
                1 + MagicNo_len + Type_len, 
                MagicNo_len + Type_len + StatusCode_len
            )
            DataLen = pkt.get_from_bits(
                1 + MagicNo_len + Type_len + StatusCode_len, 
                MagicNo_len + Type_len + StatusCode_len + DataLen_len
            )
            return StatusCode, DataLen
        except IndexError:
            raise ValueError("Invalid FileRequest header")
    
    
    def read_byte_block(self):
        """A generator that opens a file handle 
        on file_name and returns an amount of bytes equal to 
        BLOCK_SIZE.  First returns header + a part of the file as a 
        bytearray, then returns an amount of the file equal to 
        BLOCK_SIZE on each following itteration.  When the whole 
        file is transfered, the file handle is closed.  This way the 
        whole file is never read into memory.  Use this for big 
        files instead of get_bytearray()
        """
        header_bytearray = super().get_bytearray()
        self.bytes_read = 0
        data_block = bytearray()
        
        try:
            try:
                infile = open(self.file_name, 'rb')
            except IOError:
                infile = None
            
            if infile is not None and (
                self.HEADER_DICT["StatusCode"][-1] != 1 or \
                self.HEADER_DICT["DataLen"][-1] == 0):
                infile.seek(0, 2)  # Move file handle to EOF (Don't send file)
            
            # Yeilds blocks of data
            yield from self._yield_blocks(infile, header_bytearray)
        
        finally:
            if infile is not None:
                infile.close()
    
    
    def _yield_blocks(self, infile, header_bytearray):
        """Helper method of self.read_byte_block().  Takes a file 
        handle and the bytearray of the header.  Yields a 
        block of bytes equal to (or less than) BLOCK_SIZE."""
        header_len = len(header_bytearray)
        while True:
            # Take a slice of the header, max of BLOCK_SIZE
            data_block = header_bytearray[self.bytes_read : min(
                header_len, self.bytes_read + BLOCK_SIZE)]
            # If there is a file to be read, fill the rest of data_block
            if infile is not None:
                data_block.extend(infile.read(BLOCK_SIZE - len(data_block)))
            
            self.bytes_read += len(data_block)  # Incrementor
            
            if not len(data_block) > 0:
                break
            
            yield data_block
        
        raise StopIteration("Reached EOF.")        
            
        
    
    def get_bytearray(self):
        """Reads the whole file into memory and returns a 
        bytearray of header + payload."""
        file_response_data = super().get_bytearray()  # Add Header
        
        # If bad StatusCode or file doesen't exist return just the header
        if self.HEADER_DICT["StatusCode"][-1] != 1 or \
           self.HEADER_DICT["DataLen"][-1] == 0 or \
           not os.path.exists(self.file_name):
            return file_response_data
        
        with open(self.file_name, 'rb') as infile:
            file_response_data.extend(infile.read())   # Add Payload
        
        self.bytes_read = len(file_response_data)
        return file_response_data
    
    
    @staticmethod
    def is_valid_header(packet_bytearray):
        """Takes a bytearray is checks if it is a valid FileResponse 
        header.  For the method to return True: 
        MagicNo == 0x497E, 
        Type == 2, 
        StatusCode == 0 or StatusCode == 1
        """
        pkt = Packet(len(packet_bytearray)*BYTE_LEN, packet_bytearray)
        
        MagicNo_len = FileRequest.HEADER_DICT["MagicNo"][0]
        Type_len = FileRequest.HEADER_DICT["Type"][0]
        StatusCode_len = FileResponse.HEADER_DICT["StatusCode"][0]
        DataLen_len = FileResponse.HEADER_DICT["DataLen"][0]
        
        MagicNo = pkt.get_from_bits(0, MagicNo_len)
        
        Type = pkt.get_from_bits(1+MagicNo_len, MagicNo_len+Type_len)
        
        StatusCode = pkt.get_from_bits(
            1 + MagicNo_len + Type_len, 
            MagicNo_len + Type_len + StatusCode_len
        )
        
        is_valid = True
        if MagicNo != FILE_RESPONSE_MAGIC_NO:
            is_valid = False
        elif Type != FILE_RESPONSE_TYPE:
            is_valid = False        
        elif not (StatusCode == 0 or StatusCode == 1):
            is_valid = False
        
        return is_valid
    
        
    @staticmethod
    def header_bit_len():
        """Returns the len of the header in bits."""
        try:
            return sum(
                bit_len for bit_len, _ in FileResponse.HEADER_DICT.values()
            )
        except NameError:
            return 0
    
    
    @staticmethod
    def header_byte_len():
        """Returns the len of the header in bits."""
        return math.ceil(FileResponse.header_bit_len() / BYTE_LEN)    








def network_to_host(bit_len, value):
    """Convert the integer value of size bit_len to host order."""
    if (0 <= bit_len <= BYTE_LEN):
        host_order_value = value
    elif (BYTE_LEN < bit_len <= BYTE_LEN*2):
        host_order_value = socket.ntohs(value)
    elif (BYTE_LEN*2 < bit_len <= BYTE_LEN*4):
        host_order_value = socket.ntohl(value)
    else:
        raise OverflowError(
            "Can't convert greater than 32-bit to host order."
        )
    return host_order_value


def host_to_network(bit_len, value):
    """Convert the integer value of size bit_len to network order."""
    if (0 <= bit_len <= BYTE_LEN):
        net_order_value = value
    elif (BYTE_LEN < bit_len <= BYTE_LEN*2):
        net_order_value = socket.htons(value)
    elif (BYTE_LEN*2 < bit_len <= BYTE_LEN*4):
        net_order_value = socket.htonl(value)
    else:
        raise OverflowError(
            "Can't convert greater than 32-bit to network order."
        )
    return net_order_value


