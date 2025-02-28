'''
This module defines the behaviour of a client in your Chat Application
'''

import sys
import socket
from threading import Thread
from dataclasses import dataclass
import argparse


@dataclass
class Client:
    '''
    This is the main Client Class. 
    Write your code inside this class. 
    In the start() function, you will read user-input and act accordingly.
    receive_handler() function is running another thread and you have to listen 
    for incoming messages in this function.
    '''
    name: str   
    server_addr: str
    server_port: int
    sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __post_init__(self):
            """Initialize socket settings"""
            self.sock.settimeout(None)

    def start(self):
        """
        Main client function that connects to server and handles user input
        """
        try:
            self.sock.connect((self.server_addr, self.server_port))
            self.sock.send(self.name.encode())     #send username to server
            
            # Start message receiver thread
            Thread(target=self.receive_handler, daemon=True).start()
            
            while True:
                try:
                    user_input = sys.stdin.readline().strip() 
                except EOFError:
                    print("Error: No input received. Exiting client.")
                    return

                if user_input == "quit":
                    self.sock.send("quit".encode())         # notify server before quitting
                    self.sock.close()
                    break
                    
                self.sock.send(user_input.encode())             #send message to server

        except (socket.error, ConnectionResetError, KeyboardInterrupt) as e:
            print(f"Error: {e}")
            print("quitting")
        finally:            
            self.sock.close()
    
    def handle_message(self, msg):
        """Handles regular message responses"""
        parts = msg.split(" ", 2)
        if len(parts) == 3:
            print(f"msg: {parts[1]}: {parts[2].strip()}")
        else:
            print(msg.strip())

    def handle_list(self, msg):
        """Handles list command responses"""
        parts = msg.split(" ", 1)
        if len(parts) == 2:
            print(f"list: {parts[1].strip()}")
        else:
            print(msg.strip())

    def handle_file(self, msg):
        """Handles file transfer responses"""
        parts = msg.split(" ", 2)
        if len(parts) == 3:
            print(f"file: {parts[1]}: {parts[2].strip()}")
        else:
            print(msg.strip())

    def receive_handler(self):
        """
        Handles incoming messages from the server
        """
        try:
            while True:
                msg = self.sock.recv(1024).decode().strip()
                if not msg:
                    break
                    
                if msg.startswith("msg"):
                    self.handle_message(msg)
                elif msg.startswith("list:"):
                    self.handle_list(msg)
                elif msg.startswith("file:"):
                    self.handle_file(msg)
                else:
                    print(msg.strip())
                    
        except (socket.error, EOFError) as e:
            print(f"Error receiving message: {e}")
        finally:
            print("quitting")


# Do not change this part of code
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat Application Client")
    parser.add_argument(
        "-u", "--user",
        required=True,
        type=str,
        help="The username of the Client"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=15000,
        help="The server port, defaults to 15000"
    )
    parser.add_argument(
        "-a", "--address",
        type=str,
        default="localhost",
        help="The server IP or hostname, defaults to localhost"
    )

    args = parser.parse_args()
    USER_NAME = args.user
    PORT = args.port
    DEST = args.address

    S = Client(USER_NAME, DEST, PORT)
    try:
        # Start receiving Messages
        T = Thread(target=S.receive_handler)
        T.daemon = True
        T.start()
        # Start Client
        S.start()
    except (KeyboardInterrupt, SystemExit):
        print("Exception occurred. Exiting...")
        sys.exit()
