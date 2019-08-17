"""Run with 'python server.py <port number>'"""

from records import FileRequest, FileResponse, ENCODING_TYPE
import socket
from common import *
import time
import sys


def get_server_port_number():
    """Parses passed command line arguments to get the port number."""
    # Get cammand line arg and check that is exists
    try:
        port_num_str = sys.argv[1].strip()
    except IndexError:
        error(MISSING_ARG_ERR)
    
    return convert_portno_str(port_num_str)


def build_file_response(file_name): 
    if file_exists_locally(file_name):
        status_code = 1
        file_bytearray = bytearray(open(file_name, "rb").read())
        
    else:  # File doesn't exist locally
        status_code = 0
        file_bytearray = bytearray(0)
    
    print("Outgoing file len:", len(file_bytearray))
    return FileResponse(file_bytearray, status_code)



def print_sent_message(file_name, num_bytes_sent):
    """Prints a message describing what was sent to the client."""
    print(SENT_FILE_MESSAGE.format(os.path.basename(file_name), num_bytes_sent))


def server():
    serversocket = None
    client_socket = None
    
    try:
        port_num = get_server_port_number()
        
        # Create and Bind
        try:
            serversocket = socket.socket()
            serversocket.settimeout(TIMEOUT)
            serversocket.bind((LOCAL_HOST, port_num))
        except socket.gaierror:
            serversocket.close()
            error(COULDNT_BIND_ERR)
        
        # Listen
        try:
            serversocket.listen()
        except OSError:  # What error should this be?
            serversocket.close()
            error(SOCKET_LISTEN_ERR)
        
        
    
        # Accept incomming requests
        while True:
            
            # Accept incomming connection request
            client_socket, client_addr = serversocket.accept()
            client_socket.settimeout(TIMEOUT)
            
            # Recieve header from connection
            client_request_header = client_socket.recv(
                FileRequest.header_byte_len()
            )
            
            if len(client_request_header) != FileRequest.header_byte_len():
                error(INVALID_FILE_REQUEST_ERR)
            
            print("File Request nbo:", client_request_header)
            
            # Convert to host byte order
            client_request_header = FileRequest.header_to_host_byte_ord(
                client_request_header
            )
            
            print("File Request hbo:", client_request_header)
            
            # Check header validity
            if not FileRequest.is_valid_header(client_request_header):
                error(INVALID_FILE_REQUEST_ERR)
            # Extract filenameLen from header
            file_name_len = FileRequest.get_filenameLen_from_header(client_request_header)
            
            # Read just the filename from socket
            file_name_bytes = client_socket.recv(file_name_len)
            file_name = file_name_bytes.decode(ENCODING_TYPE)
            
            # Check length of recieved bytes
            if len(file_name_bytes) != file_name_len:
                error(INVALID_FILE_REQUEST_ERR)
            
            # Send FileResponse in blocks
            status_code = int(file_exists_locally(file_name))
            print("File_size =", os.path.getsize(file_name))
            file_response = FileResponse(file_name, status_code)
            try:
                num_bytes_sent = 0
                for byte_block in file_response.read_byte_block():
                    n = send_all(byte_block, client_socket)
                    num_bytes_sent += n
            except OSError:
                error(COULDNT_SEND_ERR)
            
            print_sent_message(file_name, num_bytes_sent)
            
            
                    
            
            client_socket.shutdown(socket.SHUT_WR)
            
            
            client_socket.close()
    
    except socket.timeout:
        error(TIMOUT_ERR)
    
    finally:
        print("Everything is closed.")
        if client_socket is not None:
            client_socket.close()
        if serversocket is not None:
            serversocket.close()
        
        
    
server()