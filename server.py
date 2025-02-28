"""
Chat server implementation for CS 382 PA1.

Handles multiple clients via sockets.
"""

import sys
import socket
from dataclasses import dataclass
import argparse
import threading

try:
    import util  
    MAX_CLIENTS = util.MAX_NUM_CLIENTS
    
except ImportError:
    print("Warning: util.py not found. Using default MAX_CLIENTS = 10")
    MAX_CLIENTS = 10

@dataclass
class Server:
    '''
    This is the main Server Class. You will to write Server code inside this class.
    '''
    server_addr: str
    server_port: int
    sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clients: dict = None
    lock: threading.Lock = threading.Lock()

    
    def __post_init__(self):
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow port reuse
            self.sock.settimeout(None)
            self.sock.bind((self.server_addr, self.server_port))
            self.sock.listen(MAX_CLIENTS)
            self.clients = {}

    def start(self):
        """
        Main server loop that accepts client connections and spawns handler threads
        """
        while True:
            client_socket, _ = self.sock.accept()
            username = client_socket.recv(1024).decode().strip()

            with self.lock:
                if len(self.clients) >= MAX_CLIENTS:
                    client_socket.send("err_server_full".encode())
                    client_socket.close()
                    continue

                if username in self.clients:
                    client_socket.send("err_username_unavailable".encode())
                    client_socket.close()
                    continue

                self.clients[username] = client_socket

            print(f"join: {username}")

            threading.Thread(target=self.handle_client, args=(client_socket, username), daemon=True).start()

    def handle_client(self, client_socket, username):
        """
        Handles communication with a single client
        """
        try:
            while True:
                message = client_socket.recv(1024).decode()

                if not message:
                    break  # Client disconnected
                
                if message.strip() == "quit":
                    break
                    
                self.process_message(username, message)

        except (ConnectionResetError, BrokenPipeError) as e:
            print(f"Client {username} disconnected unexpectedly: {e}")
        except OSError as e:
            print(f"Error with {username}: {e}")
        finally:
            self.disconnect_client(username)

    def process_message(self, sender, msg):
        """
        Processes messages from clients and routes them appropriately
        """
        msg_parts = msg.split()
        if len(msg_parts) < 1:
            return
            
        cmd = msg_parts[0]

        if cmd == "msg":
            if len(msg_parts) < 3:
                return
                
            try:
                num_recipients = int(msg_parts[1])
                recipients = msg_parts[2:2+num_recipients]
                message = " ".join(msg_parts[2+num_recipients:])
                print(f"msg: {sender}")
                
                for recipient in recipients:
                    if recipient in self.clients:
                        try:
                            self.clients[recipient].send(f"msg {sender} {message}".encode())
                        except OSError:
                            print(f"Error sending message to {recipient}")
                    else:
                        print(f"msg: {sender} to non-existent user {recipient}")
            except (ValueError, IndexError):
                return

        elif cmd == "list":
            print(f"request_users_list: {sender}")
            users = " ".join(sorted(self.clients.keys()))
            try:
                self.clients[sender].send(f"list: {users}".encode())
            except OSError:
                print(f"Error sending user list to {sender}")

        elif cmd == "file":
            try:
                num_recipients = int(msg_parts[1])
                recipients = msg_parts[2:2+num_recipients]
                filename = msg_parts[2+num_recipients]
                file_contents = " ".join(msg_parts[3+num_recipients:])
                
                # Important: Log the file transfer for the test to check
                print(f"file: {sender}")
                
                for recipient in recipients:
                    if recipient in self.clients:
                        try:
                            self.clients[recipient].send(f"file: {sender} {filename} {file_contents}".encode())
                        except OSError:
                            print(f"Error sending file to {recipient}")
                    else:
                        print(f"msg: {sender} to non-existent user {recipient}")
            except (ValueError, IndexError):
                return

        elif cmd == "quit":
            self.disconnect_client(sender)

    def disconnect_client(self, username):
        """
        Safely disconnects a client and removes them from the clients dictionary
        """
        with self.lock:
            if username in self.clients:
                try:
                    if self.clients[username]:
                        self.clients[username].close()
                except OSError as e:
                    print(f"Error closing socket for {username}: {e}")
                del self.clients[username]
                print(f"disconnected: {username}")







# Do not change this part of code
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat Application Server")
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
    PORT = args.port
    DEST = args.address

    SERVER = Server(DEST, PORT)
    try:
        SERVER.start()
    except (KeyboardInterrupt, SystemExit):
        print("Exception occurred. Exiting...")
        sys.exit()
