# Cloud File Storage and Publishing System

A client-server application built with Python that enables file sharing and management over TCP/IP networks. This project was developed as part of the CS408 Computer Networks course at Sabanci University.

## Features

- **Multi-Client Support**: Multiple clients can connect to the server simultaneously
- **User Authentication**: Each client has a unique username
- **File Operations**:
  - Upload text files to server
  - Download files from other users
  - Delete own files
  - View list of all available files
- **Real-time Notifications**: Users get notified when their files are downloaded
- **Graphical User Interface**: Both client and server have user-friendly GUI interfaces
- **Persistent Storage**: Files and file information persist between server restarts

## System Requirements

- Python 3.x
- tkinter (usually comes with Python)

## Project Structure

```
project/
├── client/
│   └── client.py     # Client application code
├── server/
│   ├── server.py     # Server application code
│   └── files_info.json   # File information database
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cloud-file-storage.git
cd cloud-file-storage
```

2. Ensure Python 3.x is installed on your system

## Usage

### Starting the Server

1. Run the server application:
```bash
python server/server.py
```

2. In the server GUI:
   - Enter the desired port number (default: 12345)
   - Select a storage folder for uploaded files
   - Click "Start Server"

### Running the Client

1. Run the client application:
```bash
python client/client.py
```

2. In the client GUI:
   - Enter the server's IP address (use "localhost" for local testing)
   - Enter the server's port number
   - Choose a unique username
   - Click "Connect"

### File Operations

- **Upload**: Click "Select File to Upload" and choose a text file
- **Download**: Select a file from the list and click "Download Selected File"
- **Delete**: Select your own file and click "Delete Selected File"
- **View Files**: Click "Refresh File List" to see available files

## Technical Details

- Uses TCP sockets for reliable communication
- Handles text files of any size
- Implements file ownership and access control
- Manages concurrent client connections
- Uses JSON for message passing between client and server
- Maintains persistent file storage

## Limitations

- Only supports text (.txt) files
- Files must contain ASCII characters only
- Unicode characters in filenames are not supported

## Error Handling

The system includes comprehensive error handling for:
- Connection issues
- Duplicate usernames
- File access permissions
- Invalid file types
- Network disconnections
