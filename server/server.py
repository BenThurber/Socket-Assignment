'''This contains the main function for the server.  
Run with "python server.py <port number>"

Creates a server that waits for connections from clients.  
Accepts a FileRequest and sends back a FileResponse with 
the file if it exists on the server.

To send the file to the client, the server reads the file 
locally in blocks; reading a block of BLOCK_SIZE, sending 
that block, and so on.  This way the entire file is never 
read into memory.
'''

from records import FileRequest, FileResponse, ENCODING_TYPE, BLOCK_SIZE
import socket
from common import *
import sys


def get_server_port_number():
    """Parses passed command line arguments to get the port number."""
    # Get command line arg and check that is exists
    try:
        port_num_str = sys.argv[1].strip()
    except IndexError:
        error(MISSING_ARG_ERR)
    
    return convert_portno_str(port_num_str)


def build_file_response(file_name):
    """Takes a file_name (directory) and retuns a valid 
    FileResponse object.  Checks that the file exists on 
    the server and sets the StatusCode appropriately."""
    if file_exists_locally(file_name):
        status_code = 1
        file_bytearray = bytearray(open(file_name, "rb").read())
        
    else:  # File doesn't exist locally
        status_code = 0
        file_bytearray = bytearray(0)
    
    print("Outgoing file len:", len(file_bytearray))
    return FileResponse(file_bytearray, status_code)



def print_sent_message(file_name, num_bytes_sent, success=True):
    """Prints a message describing what was sent to the client."""
    if success:
        print(SENT_FILE_MESSAGE.format(
            os.path.basename(file_name), num_bytes_sent
        ))
    else:
        print(COULDNT_SENT_FILE_MESSAGE.format(
            os.path.basename(file_name), num_bytes_sent
        ))


def main():
    """Main function to run the server from.  Needs to be 
    run from the command line.  See Module docstring."""
    server_socket = None
    client_socket = None
    
    try:
        # Get port number from command line args
        port_num = get_server_port_number()
        
        # Create and Bind
        try:
            # Create server socket
            server_socket = socket.socket()
            host_address = socket.gethostbyname(socket.gethostname())
            # Bind to host address
            server_socket.bind((host_address, port_num))
        except OSError:
            error(COULDNT_BIND_ERR)
        
        # Listen
        try:
            server_socket.listen()
        except OSError:
            error(SOCKET_LISTEN_ERR)
        
        
        
        # Continually accept() incomming requests
        while True:
            
            # Accept incomming connection request
            client_socket, client_addr = server_socket.accept()
            client_socket.settimeout(TIMEOUT)
            
            
            # Recieve header from connection
            client_request_header = recv_all(
                FileRequest.header_byte_len(), client_socket
            )
            
            # Convert to host byte order
            client_request_header = FileRequest.header_to_host_byte_ord(
                client_request_header
            )
            
            # Check header validity
            if not FileRequest.is_valid_header(client_request_header):
                error(INVALID_FILE_REQUEST_ERR, exit_all=False)
                continue
            
            
            # Extract filenameLen from header
            file_name_len = FileRequest.get_filenameLen_from_header(
                client_request_header
            )
            
            # Read just the filename from socket
            file_name_bytes = recv_all(file_name_len, client_socket)
            file_name = file_name_bytes.decode(ENCODING_TYPE)
            
            
            # Send FileResponse in blocks
            status_code = int(file_exists_locally(file_name))
            file_response = FileResponse(file_name, status_code)
            try:
                num_bytes_sent = 0
                for byte_block in file_response.read_byte_block():
                    n = send_all(byte_block, client_socket)
                    num_bytes_sent += n
            except OSError:
                error(COULDNT_SEND_ERR)
            
            
            # Close this client socket
            client_socket.close()
            
            
            # Print an informational message 
            # (differentiates between sucessful send and not sucessful)
            print_sent_message(file_name, num_bytes_sent, status_code)
                    
            
            
            
    
    except socket.timeout:
        error(TIMOUT_ERR)
    
    finally:
        if client_socket is not None:
            print("Client is closed.")
            client_socket.close()
        if server_socket is not None:
            print("Server is closed.")
            server_socket.close()
            
        
        
if __name__ == "__main__":
    main()