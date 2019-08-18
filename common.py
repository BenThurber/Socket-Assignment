"""Functions and constants that are used by (common to) both 
client.py and server.py
"""

import os

MIN_PORT_NUM = 1024
MAX_PORT_NUM = 64000

TIMEOUT = 1.0    # Timeout in seconds

BAD_PORT_NUMBER_ERR = "ERROR port number is not in not in the range {} to {} \
or it is a bad format.".format(MIN_PORT_NUM, MAX_PORT_NUM)
COULDNT_BIND_ERR = "ERROR on binding to socket."
COULDNT_CREATE_ERR = "ERROR on createing socket"
COULDNT_CONNECT_ERR = "ERROR on connecting to socket."
COULDNT_SEND_ERR = "ERROR couldn't send data on socket."
SOCKET_LISTEN_ERR = "ERROR on listening to socket."
MISSING_ARG_ERR = "ERROR missing one or more command line arguments."
FILE_ALREADY_EXISTS_ERR = "ERROR the file {} already exists locally."
CANT_CONVERT_ADRESS_ERR = "ERROR nodename nor servname provided, or not known."
TIMOUT_ERR = "ERROR timeout"
INVALID_FILE_REQUEST_ERR = "ERROR invalid FileRequest"
INVALID_FILE_RESPONSE_ERR = "ERROR invalid FileResponse"
COULDNT_WRITE_FILE_ERR = "ERROR couldn't write file to disk."
FILE_NOT_ON_SERVER_ERR = "ERROR the server couldn't retrieve the file."

SENT_FILE_MESSAGE = 'Sent "{}" to client, {} bytes sent.'
COULDNT_SENT_FILE_MESSAGE = 'The file "{}" does not exist, and could not be \
transfered.  FileResponse sent to client.  {} bytes sent.'

RECEIVED_FILE_MESSAGE = 'Received "{}" from server, {} bytes received.'
COULDNT_RECEIVE_FILE_MESSAGE = 'The file "{}" does not exist on the server, \
and could not be transfered.  FileResponse recieved from server.  {} bytes \
transfered.'



def error(message="", exit_all=True):
    """exits with an error message."""
    if exit_all:
        exit(message)
    else:
        print(message)


def send_all(data, sock):
    """Takes a bytearray and an open socket.  
    Equivalent to socket.sendall but counts and returns 
    the number of bytes transfered.  Calls socket.send() 
    until all bytes are sent."""
    sent_bytes = 0
    while sent_bytes < len(data):
        sent_bytes += sock.send(data[sent_bytes:])
    
    return sent_bytes


def recv_all(num_bytes, sock):
    """Takes a number of bytes to recieve, and an open socket.
    Calls socket.send() until all bytes are sent."""
    data = bytearray()
    next_block = bytearray()
    while len(data) < num_bytes:
        
        next_block = sock.recv(num_bytes - len(data))
        
        if len(next_block) <= 0:
            break
        
        data.extend(next_block)
    
    return data

    
def convert_portno_str(port_num):
    """Check that port number is a number is is in correct 
    range, else call error()."""
    if isinstance(port_num, int):
        return port_num
    elif isinstance(port_num, str) and port_num.isdigit() and \
         MIN_PORT_NUM <= int(port_num) <= MAX_PORT_NUM:
        return int(port_num)
    else:
        error(BAD_PORT_NUMBER_ERR)


def file_exists_locally(file_name):
    """Returns True if file_name exists AND it can be opened locally."""
    file_exists = False
    # Test if the file can be opened
    if os.path.exists(file_name):
        # Test if the file can be opened
        try:
            infile = open(file_name)
            file_exists = True
        except IOError:
            file_exists = False
        finally:
            infile.close()
        
    return file_exists