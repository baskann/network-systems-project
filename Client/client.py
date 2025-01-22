import socket
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import os

class FileClient:
    def __init__(self):
        # basic setup
        self.socket = None
        self.connected = False
        self.username = ""  # store current username
        
        # setup window
        self.window = tk.Tk()
        self.window.title("File Client")
        self.setup_gui()
        
        # where to save stuff
        self.download_folder = ""
    
    def setup_gui(self):
        # connection stuff
        conn_frame = ttk.LabelFrame(self.window, text="Connection Settings")
        conn_frame.pack(padx=5, pady=5, fill=tk.X)
        
        # ip input
        ip_frame = ttk.Frame(conn_frame)
        ip_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(ip_frame, text="Server IP:").pack(side=tk.LEFT)
        self.ip_entry = ttk.Entry(ip_frame)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        self.ip_entry.insert(0, "localhost")
        
        # port input
        port_frame = ttk.Frame(conn_frame)
        port_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(port_frame)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "12345")
        
        # username input
        user_frame = ttk.Frame(conn_frame)
        user_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(user_frame, text="Username:").pack(side=tk.LEFT)
        self.username_entry = ttk.Entry(user_frame)
        self.username_entry.pack(side=tk.LEFT, padx=5)
        
        # connect button
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_to_server)
        self.connect_btn.pack(pady=5)
        
        # file operations area
        file_frame = ttk.LabelFrame(self.window, text="File Operations")
        file_frame.pack(padx=5, pady=5, fill=tk.X)
        
        # upload button
        upload_frame = ttk.Frame(file_frame)
        upload_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(upload_frame, text="Select File to Upload", 
                  command=self.select_upload_file).pack(side=tk.LEFT, padx=5)
        
        # download folder button
        download_frame = ttk.Frame(file_frame)
        download_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(download_frame, text="Set Download Folder", 
                  command=self.select_download_folder).pack(side=tk.LEFT, padx=5)
        
        # file list area
        list_frame = ttk.LabelFrame(self.window, text="Available Files")
        list_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # file list with columns
        self.file_list = ttk.Treeview(list_frame, columns=("Filename", "Owner"), show="headings")
        self.file_list.heading("Filename", text="Filename")
        self.file_list.heading("Owner", text="Owner")
        self.file_list.column("Filename", width=200)
        self.file_list.column("Owner", width=100)
        self.file_list.pack(fill=tk.BOTH, expand=True)
        
        # file operation buttons
        ttk.Button(list_frame, text="Refresh File List", 
                  command=self.request_file_list).pack(pady=5)
        ttk.Button(list_frame, text="Download Selected File", 
                  command=self.download_selected_file).pack(pady=5)
        ttk.Button(list_frame, text="Delete Selected File", 
                  command=self.delete_selected_file).pack(pady=5)
        
        # log area
        log_frame = ttk.Frame(self.window)
        log_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.log_box = tk.Text(log_frame, height=10, width=50)
        self.log_box.pack(fill=tk.BOTH, expand=True)
    
    def connect_to_server(self):
        if not self.connected:
            try:
                # get connection info
                ip = self.ip_entry.get()
                port = int(self.port_entry.get())
                username = self.username_entry.get().strip()
                
                # check username
                if not username:
                    messagebox.showerror("Error", "Username is required")
                    return
                
                # try connecting
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((ip, port))
                
                # send username
                self.send_message({
                    "type": "connect",
                    "username": username
                })
                
                # start listening thread
                self.connected = True
                self.connect_btn.config(text="Disconnect")
                self.log(f"trying to connect as {username}...")
                
                threading.Thread(target=self.receive_messages, daemon=True).start()
                
            except Exception as e:
                self.log(f"couldn't connect: {str(e)}")
                messagebox.showerror("Error", f"Connection failed: {str(e)}")
        else:
            self.disconnect()
    
    def disconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        self.username = ""  # clear username
        self.connect_btn.config(text="Connect")
        self.log("disconnected from server")
        
        # clear file list
        for item in self.file_list.get_children():
            self.file_list.delete(item)
    
    def select_upload_file(self):
        if not self.connected:
            messagebox.showerror("Error", "connect to server first!")
            return
            
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            self.upload_file(file_path)
    
    def select_download_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_folder = folder
            self.log(f"downloads will go to: {folder}")
    
    def request_file_list(self):
        if not self.connected:
            messagebox.showerror("Error", "connect to server first!")
            return
            
        self.send_message({"type": "list_files"})
    
    def send_message(self, message):
        try:
            self.socket.send(json.dumps(message).encode())
        except Exception as e:
            self.log(f"couldn't send message: {str(e)}")
            self.disconnect()
    
    def log(self, message):
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)
    
    def run(self):
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    
    def on_closing(self):
        self.disconnect()
        self.window.destroy()
    
    def receive_messages(self):
        try:
            while self.connected:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                message = json.loads(data)
                self.handle_server_message(message)
        except Exception as e:
            if self.connected:  # only log if we didn't disconnect on purpose
                self.log(f"lost connection: {str(e)}")
            self.disconnect()
    
    def handle_server_message(self, message):
        try:
            if message['type'] == 'connect_response':
                if message['status'] == 'success':
                    self.username = message['assigned_username']
                    self.username_entry.delete(0, tk.END)
                    self.username_entry.insert(0, self.username)
                    self.log(f"connected as '{self.username}'")
                    self.request_file_list()  # get initial file list
                else:
                    error_msg = message.get('message', 'connection failed')
                    self.log(f"couldn't connect: {error_msg}")
                    messagebox.showerror("Error", error_msg)
                    self.disconnect()
            elif message['type'] == 'file_list':
                self.update_file_list(message['files'])
            elif message['type'] == 'upload_response':
                if message['status'] == 'success':
                    if message.get('overwritten', False):
                        self.log(f"overwrote file: {message['filename']}")
                    else:
                        self.log(f"uploaded file: {message['filename']}")
                    self.request_file_list()  # refresh list
                else:
                    self.log(f"upload failed: {message.get('message', 'unknown error')}")
            elif message['type'] == 'download_response':
                if message['status'] == 'success':
                    self.save_downloaded_file(message['filename'], message['content'])
                else:
                    self.log(f"download failed: {message.get('message', 'unknown error')}")
            elif message['type'] == 'delete_response':
                if message['status'] == 'success':
                    self.log(f"deleted file: {message['filename']}")
                    self.request_file_list()  # refresh list
                else:
                    self.log(f"couldn't delete: {message.get('message', 'unknown error')}")
            elif message['type'] == 'download_notification':
                self.log(f"{message['downloader']} downloaded your file: {message['filename']}")
        except Exception as e:
            self.log(f"error handling message: {str(e)}")
    
    def update_file_list(self, files):
        # clear current list
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        
        # add files to list
        for filename, owner in files.items():
            # remove username prefix from filename
            display_filename = filename[len(owner) + 1:]
            self.file_list.insert("", "end", values=(display_filename, owner))
    
    def upload_file(self, file_path):
        try:
            # check file type
            if not file_path.lower().endswith('.txt'):
                messagebox.showerror("Error", "only txt files allowed!")
                return
            
            # read file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # get filename
            filename = os.path.basename(file_path)
            
            # send to server
            self.send_message({
                "type": "upload_file",
                "filename": filename,
                "content": content
            })
            
            self.log(f"uploading: {filename}")
            
        except UnicodeDecodeError:
            messagebox.showerror("Error", "file must be text only!")
            self.log("upload failed: non-text characters found")
        except Exception as e:
            messagebox.showerror("Error", f"upload failed: {str(e)}")
            self.log(f"upload error: {str(e)}")
    
    def save_downloaded_file(self, filename, content):
        try:
            if not self.download_folder:
                raise Exception("set a download folder first!")
            
            file_path = os.path.join(self.download_folder, filename)
            with open(file_path, 'w') as f:
                f.write(content)
            
            self.log(f"saved: {filename}")
        except Exception as e:
            self.log(f"couldn't save file: {str(e)}")
    
    def download_selected_file(self):
        selected_item = self.file_list.selection()
        if not selected_item:
            messagebox.showerror("Error", "select a file first!")
            return
        
        # get file info
        display_filename = self.file_list.item(selected_item[0], 'values')[0]
        owner = self.file_list.item(selected_item[0], 'values')[1]
        
        # make server filename
        full_filename = f"{owner}_{display_filename}"
        self.request_file_download(full_filename)
    
    def request_file_download(self, filename):
        if not self.connected:
            messagebox.showerror("Error", "connect to server first!")
            return
        
        if not self.download_folder:
            messagebox.showerror("Error", "set a download folder first!")
            return
        
        self.send_message({
            "type": "download_file",
            "filename": filename
        })
        self.log(f"downloading: {filename}")
    
    def delete_selected_file(self):
        selected_item = self.file_list.selection()
        if not selected_item:
            messagebox.showerror("Error", "select a file first!")
            return
        
        # get file info
        display_filename = self.file_list.item(selected_item[0], 'values')[0]
        owner = self.file_list.item(selected_item[0], 'values')[1]
        
        # check ownership
        if owner != self.username:
            messagebox.showerror("Error", "you can only delete your own files!")
            return
        
        # confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Delete {display_filename}?"):
            full_filename = f"{owner}_{display_filename}"
            self.request_file_delete(full_filename)
    
    def request_file_delete(self, filename):
        if not self.connected:
            messagebox.showerror("Error", "connect to server first!")
            return
        
        self.send_message({
            "type": "delete_file",
            "filename": filename
        })
        self.log(f"trying to delete: {filename}")

if __name__ == "__main__":
    client = FileClient()
    client.run()