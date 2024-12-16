import tkinter as tk
import socket
import threading

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.initUI()
        self.buffsize = 1024
        self.serverSoc = None
        self.serverStatus = 0
        self.allClients = {}
        self.counter = 0
        self.clientNames = {}

    def initUI(self):
        self.root.title("P2P Chat Application")
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
        parentFrame = tk.Frame(self.root, bg="#f8d7f7")  # Pink muda
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
        ipGroup = tk.Frame(parentFrame, bg="#fbd4e8")  # Pink muda
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
        self.receivedChats = tk.Text(readChatGroup, bg="#ffffff", width=60, height=20, state=tk.DISABLED, font=("Arial", 12))
        self.friends.grid(row=0, column=0, sticky=tk.W + tk.N + tk.S, padx=(0, 10))
        self.receivedChats.grid(row=0, column=1, sticky=tk.E + tk.N + tk.S)
        return readChatGroup

    def create_write_chat_group(self, parentFrame):
        writeChatGroup = tk.Frame(parentFrame)
        self.chatVar = tk.StringVar()
        self.chatField = tk.Entry(writeChatGroup, width=70, textvariable=self.chatVar, font=("Arial", 12))  # Lebar ditambah
        sendChatButton = tk.Button(writeChatGroup, text="Send", width=12, command=self.handleSendChat, bg="#ff77b2", fg="white", font=("Arial", 12))

        self.chatField.grid(row=0, column=0, sticky=tk.W, padx=(5, 5))
        sendChatButton.grid(row=0, column=1, padx=10, columnspan=2, sticky=tk.E)  # Memastikan tombol cukup lebar dan tidak terpotong

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
            threading.Thread(target=self.listenClients).start()  # Use threading
            self.serverStatus = 1
            self.name = self.nameVar.get().strip()
            if not self.name:
                self.setStatus("Please enter a valid name before setting up the server")
            return
        except:
            self.setStatus("Error setting up server")

    def listenClients(self):
        while True:
            clientsoc, clientaddr = self.serverSoc.accept()
            self.setStatus(f"Client connected from {clientaddr}")
            self.addClient(clientsoc, clientaddr)
            threading.Thread(target=self.handleClientMessages, args=(clientsoc, clientaddr)).start()  # Use threading
        self.serverSoc.close()

    def handleAddClient(self):
        if self.serverStatus == 0:
            self.setStatus("Set server address first")
            return
        
        clientaddr = (self.clientIPVar.get().replace(' ', ''), int(self.clientPortVar.get().replace(' ', '')))
        try:
            clientsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientsoc.connect(clientaddr)
            self.setStatus(f"Connected to client on {clientaddr}")
            self.addClient(clientsoc, clientaddr)
            self.clientNames[clientaddr] = self.nameVar.get().strip()
            threading.Thread(target=self.handleClientMessages, args=(clientsoc, clientaddr)).start()  # Use threading
        except:
            self.setStatus("Error connecting to client")

    def handleClientMessages(self, clientsoc, clientaddr):
        while True:
            try:
                data = clientsoc.recv(self.buffsize)
                if not data:
                    break
                self.addChat("", data.decode('utf-8'))
            except:
                break
        self.removeClient(clientsoc, clientaddr)
        clientsoc.close()
        self.setStatus(f"Client disconnected from {clientaddr}")

    def handleSendChat(self):
        if self.serverStatus == 0:
            self.setStatus("Set server address first")
            return
        msg = self.chatVar.get()
        if not msg.strip():
            return
        self.addChat(self.name, msg)
        full_message = f"{self.name}: {msg}"  # Format pesan dengan nama pengirim
        for client in self.allClients.keys():
            try:
                client.send(full_message.encode('utf-8'))  # Kirim pesan ke client
            except:
                self.setStatus(f"Error sending message to {client}")
    
        self.chatVar.set("")

    def addChat(self, client, msg):
        self.receivedChats.config(state=tk.NORMAL)
        self.receivedChats.insert("end", f"{client}: {msg}\n")
        self.receivedChats.config(state=tk.DISABLED)

    def addClient(self, clientsoc, clientaddr):
        self.allClients[clientsoc] = self.counter
        self.counter += 1
        name = self.clientNames.get(clientaddr, clientaddr)
        self.friends.insert(self.counter, f"{clientaddr}")

    def removeClient(self, clientsoc, clientaddr):
        self.friends.delete(self.allClients[clientsoc])
        del self.allClients[clientsoc]

    def setStatus(self, msg):
        self.statusLabel.config(text=msg)

def main():
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()

if __name__ == '__main__':
    main()
