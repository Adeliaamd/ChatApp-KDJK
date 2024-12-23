import tkinter as tk
from tkinter import filedialog
import socket
import threading
from cryptography.fernet import Fernet
import os

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.initUI()
        self.buffsize = 1024 * 10  # Meningkatkan ukuran buffer
        self.serverSoc = None
        self.serverStatus = 0
        self.allClients = {}
        self.counter = 0
        self.clientNames = {}
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)

    def initUI(self):
        self.root.title("P2P Chat Application with File Sharing")
        ScreenSizeX = self.root.winfo_screenwidth()
        ScreenSizeY = self.root.winfo_screenheight()
        self.FrameSizeX = 800
        self.FrameSizeY = 600
        FramePosX = int((ScreenSizeX - self.FrameSizeX) / 2)
        FramePosY = int((ScreenSizeY - self.FrameSizeY) / 2)
        self.root.geometry(f"{self.FrameSizeX}x{self.FrameSizeY}+{FramePosX}+{FramePosY}")
        self.root.resizable(width=False, height=False)

        padX = 10
        padY = 10
        parentFrame = tk.Frame(self.root, bg="#f8d7f7")
        parentFrame.grid(padx=padX, pady=padY, stick=tk.E + tk.W + tk.N + tk.S)

        ipGroup = self.create_ip_group(parentFrame)
        readChatGroup = self.create_read_chat_group(parentFrame)
        writeChatGroup = self.create_write_chat_group(parentFrame)

        self.statusLabel = tk.Label(parentFrame, bg="#f8d7f7", fg="black", font=("Arial", 10))
        bottomLabel = tk.Label(parentFrame, text="Created by Oppa Neeman The Gank", bg="#f8d7f7", font=("Arial", 10, "italic"))

        ipGroup.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        readChatGroup.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        writeChatGroup.grid(row=2, column=0, pady=10, sticky="ew")
        self.statusLabel.grid(row=3, column=0, pady=(10, 0), sticky="ew")
        bottomLabel.grid(row=4, column=0, pady=10, sticky="ew")

    def create_ip_group(self, parentFrame):
        ipGroup = tk.Frame(parentFrame, bg="#fbd4e8")
        serverLabel = tk.Label(ipGroup, text="Set: ", bg="#fbd4e8", font=("Arial", 10))
        self.nameVar = tk.StringVar()
        self.nameVar.set("UserName")
        nameField = tk.Entry(ipGroup, width=10, textvariable=self.nameVar)
        self.serverIPVar = tk.StringVar()
        self.serverIPVar.set("127.0.0.1")
        serverIPField = tk.Entry(ipGroup, width=15, textvariable=self.serverIPVar)
        self.serverPortVar = tk.StringVar()
        self.serverPortVar.set("8090")
        serverPortField = tk.Entry(ipGroup, width=5, textvariable=self.serverPortVar)
        serverSetButton = tk.Button(ipGroup, text="Set", width=10, command=self.handleSetServer, bg="#ff77b2", fg="white")

        addClientLabel = tk.Label(ipGroup, text="Add friend: ", bg="#fbd4e8", font=("Arial", 10))
        self.clientIPVar = tk.StringVar()
        self.clientIPVar.set("127.0.0.1")
        clientIPField = tk.Entry(ipGroup, width=15, textvariable=self.clientIPVar)
        self.clientPortVar = tk.StringVar()
        self.clientPortVar.set("8091")
        clientPortField = tk.Entry(ipGroup, width=5, textvariable=self.clientPortVar)
        clientSetButton = tk.Button(ipGroup, text="Add", width=10, command=self.handleAddClient, bg="#ff77b2", fg="white")

        serverLabel.grid(row=0, column=0)
        nameField.grid(row=0, column=1)
        serverIPField.grid(row=0, column=2)
        serverPortField.grid(row=0, column=3)
        serverSetButton.grid(row=0, column=4, padx=5)
        addClientLabel.grid(row=0, column=5)
        clientIPField.grid(row=0, column=6)
        clientPortField.grid(row=0, column=7)
        clientSetButton.grid(row=0, column=8, padx=5)

        return ipGroup

    def create_read_chat_group(self, parentFrame):
        readChatGroup = tk.Frame(parentFrame)
        self.friends = tk.Listbox(readChatGroup, bg="#fce4ec", width=30, height=20, font=("Arial", 12))
        self.chatCanvas = tk.Canvas(readChatGroup, bg="#ffffff", width=450, height=400)
        self.chatFrame = tk.Frame(self.chatCanvas, bg="#ffffff")
        self.chatScrollbar = tk.Scrollbar(readChatGroup, orient="vertical", command=self.chatCanvas.yview)
        self.chatCanvas.configure(yscrollcommand=self.chatScrollbar.set)

        self.chatCanvas.create_window((0, 0), window=self.chatFrame, anchor="nw")
        self.chatFrame.bind("<Configure>", lambda e: self.chatCanvas.configure(scrollregion=self.chatCanvas.bbox("all")))

        self.friends.grid(row=0, column=0, sticky=tk.W + tk.N + tk.S, padx=(0, 10))
        self.chatCanvas.grid(row=0, column=1, sticky=tk.E + tk.N + tk.S)
        self.chatScrollbar.grid(row=0, column=2, sticky=tk.N + tk.S)

        return readChatGroup

    def create_write_chat_group(self, parentFrame):
        writeChatGroup = tk.Frame(parentFrame)
        self.chatVar = tk.StringVar()
        self.chatField = tk.Entry(writeChatGroup, width=50, textvariable=self.chatVar, font=("Arial", 12))
        sendChatButton = tk.Button(writeChatGroup, text="Send", width=12, command=self.handleSendChat, bg="#ff77b2", fg="white", font=("Arial", 12))
        sendFileButton = tk.Button(writeChatGroup, text="Send File", width=12, command=self.handleSendFile, bg="#ff77b2", fg="white", font=("Arial", 12))

        self.chatField.grid(row=0, column=0, sticky=tk.W, padx=(5, 5))
        sendChatButton.grid(row=0, column=1, padx=10)
        sendFileButton.grid(row=0, column=2, padx=10)

        return writeChatGroup

    def handleSetServer(self):
        if self.serverSoc is not None:
            self.serverSoc.close()
            self.serverSoc = None
            self.serverStatus = 0

        serveraddr = (self.serverIPVar.get().replace(' ', ''), int(self.serverPortVar.get().replace(' ', '')))

        try:
            self.serverSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serverSoc.bind(serveraddr)
            self.serverSoc.listen(5)
            self.setStatus(f"Server listening on {serveraddr}")
            threading.Thread(target=self.listenClients, daemon=True).start()
            self.serverStatus = 1
            self.name = self.nameVar.get().strip()
            if not self.name:
                self.setStatus("Please enter a valid name before setting up the server")
            return
        except Exception as e:
            self.setStatus(f"Error setting up server: {e}")

    def listenClients(self):
        while True:
            try:
                clientsoc, clientaddr = self.serverSoc.accept()
                clientsoc.send(self.encryption_key)
                self.setStatus(f"Client connected from {clientaddr}")
                self.addClient(clientsoc, clientaddr)
                threading.Thread(target=self.handleClientMessages, args=(clientsoc, clientaddr), daemon=True).start()
            except Exception as e:
                self.setStatus(f"Error accepting client: {e}")
                break

    def handleAddClient(self):
        if self.serverStatus == 0:
            self.setStatus("Set server address first")
            return

        clientaddr = (self.clientIPVar.get().replace(' ', ''), int(self.clientPortVar.get().replace(' ', '')))
        try:
            clientsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientsoc.connect(clientaddr)
            self.encryption_key = clientsoc.recv(self.buffsize)
            self.cipher = Fernet(self.encryption_key)
            self.setStatus(f"Connected to client on {clientaddr}")
            self.addClient(clientsoc, clientaddr)
            self.clientNames[clientaddr] = self.nameVar.get().strip()
            threading.Thread(target=self.handleClientMessages, args=(clientsoc, clientaddr), daemon=True).start()
        except Exception as e:
            self.setStatus(f"Error connecting to client: {e}")

    def handleClientMessages(self, clientsoc, clientaddr):
        while True:
            try:
                data = clientsoc.recv(self.buffsize)
                if not data:
                    continue
                if data.startswith(b'FILE:'):
                    try:
                        file_name, file_data = data[5:].split(b'|', 1)
                        with open(file_name.decode('utf-8'), 'wb') as f:
                            f.write(file_data)
                        self.addChat(clientaddr, f"File received: {file_name.decode('utf-8')}")
                        # Kirim konfirmasi setelah file diterima
                        clientsoc.send(self.cipher.encrypt(f"File {file_name.decode('utf-8')} received successfully".encode('utf-8')))
                    except Exception as e:
                        self.setStatus(f"Error processing file from {clientaddr}: {e}")
                else:
                    try:
                        decrypted_msg = self.cipher.decrypt(data).decode('utf-8')
                        self.addChat(clientaddr, decrypted_msg)
                    except Exception as e:
                        self.setStatus(f"Error decrypting message from {clientaddr}: {e}")
            except Exception as e:
                self.setStatus(f"Connection with {clientaddr} lost: {e}")
                break  # Pastikan thread berhenti jika koneksi putus

    def handleSendChat(self):
        if self.serverStatus == 0:
            self.setStatus("Set server address first")
            return
        msg = self.chatVar.get()
        if not msg.strip():
            return
        self.addChat(self.name, msg, True)
        full_message = f"{self.name}: {msg}"
        encrypted_msg = self.cipher.encrypt(full_message.encode('utf-8'))
        for client in self.allClients.keys():
            try:
                client.send(encrypted_msg)
            except:
                self.setStatus(f"Error sending message to {client}")
        self.chatVar.set("")

    def handleSendFile(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        try:
            file_name = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                file_data = f.read()
            file_message = f"FILE:{file_name}|".encode('utf-8') + file_data
            for client in self.allClients.keys():
                client.send(file_message)
            self.addChat(self.name, f"File sent: {file_name}", True)
        except Exception as e:
            self.setStatus(f"Error sending file: {str(e)}")

    def addChat(self, client, msg, is_self=False):
        bubble = tk.Label(self.chatFrame, text=msg, wraplength=300, justify="left",
                          bg="#ff77b2" if is_self else "#fce4ec", fg="black", font=("Arial", 10), padx=10, pady=5)
        bubble.pack(anchor="e" if is_self else "w", pady=5)
        self.chatCanvas.update_idletasks()
        self.chatCanvas.yview_moveto(1)

    def addClient(self, clientsoc, clientaddr):
        self.allClients[clientsoc] = self.counter
        self.counter += 1
        name = self.clientNames.get(clientaddr, clientaddr)
        self.friends.insert(self.counter, f"{clientaddr}")

    def setStatus(self, msg):
        self.statusLabel.config(text=msg)

def main():
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()

if __name__ == '__main__':
    main()
