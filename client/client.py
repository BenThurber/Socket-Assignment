'''This contains the main function for the client.
Run with "python client.py <address> <port number> <file name>"

Runs a client that sends a FileRequest to a server.  The client then 

'''

from records import FileRequest, FileResponse, BLOCK_SIZE
import socket
from common import *
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



def _add_directory_for(file_name):
    """Takes a relative file directory, and if the directory 
    where the file resides does not exist, it creates that 
    directory to put the file in."""
    base_dir = os.path.dirname(file_name)
    try:
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
    except FileNotFoundError:
        pass


def download_file_from_socket(file_name, client_socket, file_size):
    """Takes a file_name (directory) and a socket. And downloads 
    the file from the socket in blocks.  Assumes the next byte 
    from the socket is the first byte of the file."""
    outfile = None
    try:
        # Make sure there is a directory to put the file in
        _add_directory_for(file_name)  
        
        outfile = open(file_name, 'wb')
        
        downloaded_bytes = 0
        reached_EOF = False
        while not reached_EOF:
            
            #data_block acts as a buffer
            data_block = client_socket.recv(BLOCK_SIZE)
            
            if data_block is None:
                reached_EOF = True
                break
            
            # Have we recieved the whole file?
            if downloaded_bytes + len(data_block) >= file_size:
                print("Less than Block", len(data_block))
                reached_EOF = True
            
            outfile.write(data_block)
            downloaded_bytes += len(data_block)
            print("downloaded {} bytes".format(downloaded_bytes))
        
    except socket.timeout:
        error(TIMOUT_ERR)
    except IOError:
        error(COULDNT_WRITE_FILE_ERR)
    finally:
        if outfile is not None:
            outfile.close()
        if client_socket is not None:
            client_socket.close()
    
    return downloaded_bytes



def print_recieved_message(file_name, num_bytes_received, success=True):
    """Prints a message describing what was recieved from the 
    server."""
    if success:
        print(RECEIVED_FILE_MESSAGE.format(
            os.path.basename(file_name), num_bytes_received
        ))
    else:
        print(COULDNT_RECEIVE_FILE_MESSAGE.format(
            os.path.basename(file_name), num_bytes_received
        ))



def main():
    """Main function to run the client.  Needs to be 
    run from the command line.  See Module docstring."""    
    client_socket = None
    try:
        
        # Get command line arguments
        address_str, port_num, file_name = get_address_portno_filename()
        
        
        # Get address from address string
        try:
            address = socket.getaddrinfo(address_str, port_num)
        except OSError:
            error(CANT_CONVERT_ADRESS_ERR)
        
        
        # Check that the requested file doesen't already exist locally
        if file_exists_locally(file_name):
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
            #n_bytes_sent = send_all(file_request.get_bytearray(), client_socket)
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
        
        
        # Extract status and DataLen from header.
        status, DataLen = FileResponse.get_status_DataLen(
            server_file_response_header
        )
        
        
        # Is there a file following the header?
        if status == 1:
            # Write bytearray to local file
            n_bytes = download_file_from_socket(file_name, client_socket, DataLen)
        else:
            # No file data downloaded
            n_bytes = 0
        # Find: total-bytes = header_bytes + file_bytes
        total_bytes_recieved = len(server_file_response_header) + n_bytes
        
        
        # Print an informational message 
        # (differentiates between sucessful send and not sucessful)
        print_recieved_message(file_name, total_bytes_recieved, status)
        
        
    except socket.timeout:
        error(TIMOUT_ERR)
    finally:
        if client_socket is not None:
            client_socket.close()
        


       



if __name__ == "__main__":
    main()