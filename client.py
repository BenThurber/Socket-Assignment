"""Run with 'python client.py <address> <port number> <file name>'"""
from records import FileRequest, FileResponse
from records import FILE_REQUEST_MAGIC_NO, FILE_RESPONSE_MAGIC_NO
import socket
from common import *
import time
import sys
import os


def get_address_portno_filename():
    """Gets the address, port number and file name from the 
    command line.  Returns tuple: (address_str, port_num, file_name)"""
    try:
        address_str = sys.argv[1].strip()
        port_num_str = sys.argv[2].strip()
        file_name = sys.argv[3].strip()
    except IndexError:
        error(MISSING_ARG_ERR)
    
    port_num = convert_portno_str(port_num_str)
    
    return address_str, port_num, file_name




def download_file_from_socket(file_name, client_socket, file_size):
    """Takes a file_name (directory) and a socket. And downloads 
    the file from the socket in blocks.  Assumes the next byte 
    from the socket is the first byte of the file."""
    try:
        outfile = open(file_name, 'wb')
        
        downloaded_bytes = 0
        reached_EOF = False
        while not reached_EOF:
            
            data_block = client_socket.recv(BLOCK_SIZE)  #data_block acts as a buffer
            
            if data_block is None:   # Nessesary?
                reached_EOF = True
                break
            if downloaded_bytes + len(data_block) >= file_size:    # Have we recieved the whole file?
                print("Less than Block", len(data_block))
                reached_EOF = True
            
            outfile.write(data_block)
            downloaded_bytes += len(data_block)
            print("downloaded {} bytes".format(downloaded_bytes))
            #time.sleep(SMALL_TIME)
        
    except socket.timeout:
        error(TIMOUT_ERR)
    except IOError:
        error(COULDNT_WRITE_FILE_ERR)
    finally:
        outfile.close()
        client_socket.close() 






def client():
    client_socket = None
    try:
        
        # Get command line arguments
        address_str, port_num, file_name = get_address_portno_filename()
        
        # Get address from address string
        try:
            address = socket.getaddrinfo(address_str, port_num)  # Change to parellel assignment?
        except OSError:
            error(CANT_CONVERT_ADRESS_ERR)
        
        # Check that the requested file doesen't already exist locally
        #if file_exists_locally(file_name):
        if False:  # Temp
            error(FILE_ALREADY_EXISTS_ERR.format(os.path.basename(file_name)))        
        
        # Create a socket
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(TIMEOUT)
        except OSError:
            error(COULDNT_CREATE_ERR)
        
        # Try to connect
        try:
            client_socket.connect(address[0][4])
        except (OSError, ConnectionRefusedError):
            error(COULDNT_CONNECT_ERR)
        
        # Build a FileRequest
        file_request = FileRequest(file_name)
        print("File Request:", file_request.get_bytearray())
        
        # Send FileRequest
        try:
            n_bytes_sent = client_socket.sendall(file_request.get_bytearray())
            print(n_bytes_sent, "Bytes sent")
        except OSError:
            error(COULDNT_SEND_ERR)
        
        # Recieve a number of bytes equal to the length of the header
        server_file_response_header = client_socket.recv(FileResponse.header_byte_len())
        server_file_response_header = FileResponse.header_to_host_byte_ord(
            server_file_response_header
        )
        print("Response header:", server_file_response_header)
        for byte in server_file_response_header:
            print(byte)
        
        # Check header validity
        if not FileResponse.is_valid_header(server_file_response_header):
            error(INVALID_FILE_RESPONSE_ERR)
        
        # Extract DataLen from header  Do I need this if I'm recieving in blocks?
        status,DataLen = FileResponse.get_status_DataLen(server_file_response_header)
        print("Header DataLen:", DataLen)
        
        ## Recieve an amount of bytes equal to the length of the file (Temp?)
        #file_bytearray = client_socket.recv(DataLen)
        
        # Write bytearray to local file
        new_filename = os.path.join(os.path.dirname(file_name), "new_"+os.path.basename(file_name))
        #write_bytes_to_file(new_filename, file_bytearray)
        if status == 1:
            download_file_from_socket(new_filename, client_socket, DataLen)
        else:
            error(FILE_NOT_ON_SERVER_ERR)
        
        
    except socket.timeout:
        error(TIMOUT_ERR)
    finally:
        print("Everything is closed.")
        if client_socket is not None and not client_socket._closed:
            #client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        


       




client()