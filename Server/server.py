import socket
import threading
import tkinter as tk
from tkinter import filedialog, ttk
import json
import os

class FileServer:
    def __init__(self):
        # file info path
        self.files_info_path = "files_info.json"
        
        # server state
        self.clients = {}  # active clients
        self.files_info = {}  # file info
        self.server_socket = None
        self.running = False
        
        # gui setup
        self.window = tk.Tk()
        self.window.title("File Server")
        self.setup_gui()
        
        # load file data
        self.load_files_info()
    
    def setup_gui(self):
        # port config
        port_frame = ttk.Frame(self.window)
        port_frame.pack(padx=5, pady=5, fill=tk.X)
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(port_frame, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "12345")
        
        # folder selection
        folder_frame = ttk.Frame(self.window)
        folder_frame.pack(padx=5, pady=5, fill=tk.X)
        ttk.Label(folder_frame, text="Storage Folder:").pack(side=tk.LEFT)
        self.folder_path = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_path).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(folder_frame, text="Browse", command=self.select_folder).pack(side=tk.LEFT)
        
        # server controls
        control_frame = ttk.Frame(self.window)
        control_frame.pack(padx=5, pady=5, fill=tk.X)
        self.start_button = ttk.Button(control_frame, text="Start Server", command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # log display
        log_frame = ttk.Frame(self.window)
        log_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.log_box = tk.Text(log_frame, height=10, width=50)
        self.log_box.pack(fill=tk.BOTH, expand=True)
    
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.log(f"Storage folder set to: {folder}")
    
    def start_server(self):
        if not self.running:
            try:
                port = int(self.port_entry.get())
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind(('', port))
                self.server_socket.listen(5)
                self.running = True
                self.start_button.config(text="Stop Server")
                self.log(f"Server started on port {port}")
                
                # accept connections
                threading.Thread(target=self.accept_connections, daemon=True).start()
            except Exception as e:
                self.log(f"Error starting server: {str(e)}")
        else:
            self.stop_server()
    
    def log(self, message):
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)
    
    def run(self):
        self.window.mainloop()
    
    def load_files_info(self):
        try:
            if os.path.exists(self.files_info_path):
                with open(self.files_info_path, 'r') as f:
                    self.files_info = json.load(f)
                self.log("Loaded existing files information")
            else:
                self.files_info = {}
                self.log("No existing files information found")
        except Exception as e:
            self.log(f"Error loading files info: {str(e)}")
            self.files_info = {}
    
    def save_files_info(self):
        try:
            with open(self.files_info_path, 'w') as f:
                json.dump(self.files_info, f)
        except Exception as e:
            self.log(f"Error saving files info: {str(e)}")
    
    def stop_server(self):
        if self.running:
            try:
                self.running = False
                if self.server_socket:
                    self.server_socket.close()
                
                # close client connections
                for client in self.clients.values():
                    try:
                        client['socket'].close()
                    except:
                        pass
                
                self.clients.clear()
                self.start_button.config(text="Start Server")
                self.log("Server stopped")
                
                # save files info
                self.save_files_info()
                
            except Exception as e:
                self.log(f"Error stopping server: {str(e)}")
    
    def accept_connections(self):
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                threading.Thread(target=self.handle_client,
                              args=(client_socket, address),
                              daemon=True).start()
                self.log(f"New connection from {address}")
            except:
                if self.running:
                    self.log("Error accepting connection")
                break
    
    def handle_client(self, client_socket, address):
        try:
            data = client_socket.recv(1024).decode()
            message = json.loads(data)
            
            if message['type'] == 'connect':
                requested_username = message['username']
                
                # check username
                if requested_username in self.clients or any(
                    requested_username == name.split('(')[0] 
                    for name in self.clients.keys()
                ):
                    client_socket.send(json.dumps({
                        "type": "connect_response",
                        "status": "error",
                        "message": "Username is already taken. Please choose a unique name."
                    }).encode())
                    self.log(f"Connection rejected - username '{requested_username}' is taken")
                    return
                
                # username available
                username = requested_username
                self.clients[username] = {
                    "socket": client_socket,
                    "address": address
                }
                
                self.log(f"Client {username} connected from {address}")
                
                # send success response
                client_socket.send(json.dumps({
                    "type": "connect_response",
                    "status": "success",
                    "assigned_username": username
                }).encode())
                
                # handle client messages
                while self.running:
                    data = client_socket.recv(1024).decode()
                    if not data:
                        break
                    self.handle_client_message(username, json.loads(data))
                    
        except Exception as e:
            self.log(f"Error handling client {address}: {str(e)}")
        finally:
            if 'username' in locals() and username in self.clients:
                del self.clients[username]
            try:
                client_socket.close()
            except:
                pass
            self.log(f"Client {address} disconnected")
    
    def generate_unique_username(self, base_username):
        if base_username not in self.clients:
            return base_username
        
        counter = 1
        while f"{base_username}({counter})" in self.clients:
            counter += 1
        
        return f"{base_username}({counter})"
    
    def handle_client_message(self, username, message):
        try:
            if message['type'] == 'list_files':
                self.send_file_list(username)
            elif message['type'] == 'upload_file':
                self.handle_file_upload(username, message)
            elif message['type'] == 'download_file':
                self.handle_file_download(username, message)
            elif message['type'] == 'delete_file':
                self.handle_file_delete(username, message)
        except Exception as e:
            self.log(f"Error handling message from {username}: {str(e)}")
    
    def handle_file_upload(self, username, message):
        try:
            filename = message['filename']
            content = message['content']
            
            # create storage folder
            storage_folder = self.folder_path.get()
            if not storage_folder:
                raise Exception("Storage folder not set")
            
            if not os.path.exists(storage_folder):
                os.makedirs(storage_folder)
            
            # save file with username prefix
            full_filename = f"{username}_{filename}"
            file_path = os.path.join(storage_folder, full_filename)
            
            # check if file exists
            is_overwriting = False
            if full_filename in self.files_info:
                if self.files_info[full_filename] == username:
                    is_overwriting = True
                    self.log(f"File '{filename}' is being overwritten by {username}")
                else:
                    raise Exception("A file with this name exists but is owned by another user")
            
            # save the file
            with open(file_path, 'w') as f:
                f.write(content)
            
            # update files info
            self.files_info[full_filename] = username
            self.save_files_info()
            
            # send success response
            self.clients[username]['socket'].send(json.dumps({
                "type": "upload_response",
                "status": "success",
                "filename": filename,
                "overwritten": is_overwriting
            }).encode())
            
            # log message
            if is_overwriting:
                self.log(f"File '{filename}' overwritten by {username}")
            else:
                self.log(f"File '{filename}' uploaded by {username}")
            
            # update clients
            self.broadcast_file_list()
            
        except Exception as e:
            self.log(f"Error handling file upload from {username}: {str(e)}")
            # send error response
            self.clients[username]['socket'].send(json.dumps({
                "type": "upload_response",
                "status": "error",
                "message": str(e)
            }).encode())
    
    def handle_file_download(self, username, message):
        try:
            filename = message['filename']
            
            # check if file exists
            if filename not in self.files_info:
                raise Exception("File not found")
            
            # get file path
            storage_folder = self.folder_path.get()
            file_path = os.path.join(storage_folder, filename)
            
            # read file content
            with open(file_path, 'r') as f:
                content = f.read()
            
            # send file content
            self.clients[username]['socket'].send(json.dumps({
                "type": "download_response",
                "status": "success",
                "filename": filename,
                "content": content
            }).encode())
            
            self.log(f"File '{filename}' sent to {username}")
            
            # notify uploader
            uploader = self.files_info[filename]
            if uploader in self.clients and uploader != username:
                self.clients[uploader]['socket'].send(json.dumps({
                    "type": "download_notification",
                    "filename": filename,
                    "downloader": username
                }).encode())
                self.log(f"Uploader '{uploader}' notified about download by '{username}'")
            
        except Exception as e:
            self.log(f"Error handling file download for {username}: {str(e)}")
            # send error response
            self.clients[username]['socket'].send(json.dumps({
                "type": "download_response",
                "status": "error",
                "message": str(e)
            }).encode())
    
    def handle_file_delete(self, username, message):
        try:
            filename = message['filename']
            
            # check if file exists
            if filename not in self.files_info or self.files_info[filename] != username:
                raise Exception("File not found or permission denied")
            
            # get file path
            storage_folder = self.folder_path.get()
            file_path = os.path.join(storage_folder, filename)
            
            # delete the file
            os.remove(file_path)
            
            # remove from files info
            del self.files_info[filename]
            self.save_files_info()
            
            # send success response
            self.clients[username]['socket'].send(json.dumps({
                "type": "delete_response",
                "status": "success",
                "filename": filename
            }).encode())
            
            self.log(f"File '{filename}' deleted by {username}")
            
            # update clients
            self.broadcast_file_list()
            
        except Exception as e:
            self.log(f"Error handling file delete for {username}: {str(e)}")
            # send error response
            self.clients[username]['socket'].send(json.dumps({
                "type": "delete_response",
                "status": "error",
                "message": str(e)
            }).encode())
    
    def broadcast_file_list(self):
        for client in self.clients.values():
            try:
                client['socket'].send(json.dumps({
                    "type": "file_list",
                    "files": self.files_info
                }).encode())
            except Exception as e:
                self.log(f"Error broadcasting file list: {str(e)}")
    
    def send_file_list(self, username):
        try:
            client_socket = self.clients[username]['socket']
            client_socket.send(json.dumps({
                "type": "file_list",
                "files": self.files_info
            }).encode())
        except Exception as e:
            self.log(f"Error sending file list to {username}: {str(e)}")

if __name__ == "__main__":
    server = FileServer()
    server.run()