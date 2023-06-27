import socket
# Socket for networking
import tkinter as tk
from tkinter import ttk
# Tkinter used as interface
import threading
# Threading used for multithreading
from lib.client import Client as client

class ChatApp:
    def __init__(self) -> None:
        super(ChatApp, self).__init__()
        self.is_connected = False
        self.receiver_ip = None
        self.receiver_port = None
        self.peer_ip = None
        self.peer_port = None
        self.peer_nick = None
        self.nick = "Anon"
        self.connected_peers = 0
    def send_message(self, event = None):
        message = message_entry.get()
        message_entry.delete(0, tk.END)
        ### Message_entry.get() was used to retrieve what has been entered on the message box.

        if message.isspace() or len(message) == 0:
            message_box.insert(tk.END, "Please enter a message.\n")
        elif message.startswith("/connect"):
            connect_args = message.split()
            if len(connect_args) >= 3:
                self.peer_ip = connect_args[1]
                self.peer_port = int(connect_args[2])
                if len(connect_args) == 4:
                    self.nick = connect_args[3]
                self.connect_to_peer(self.peer_ip, int(self.peer_port))

        ### checking for the command. /connect. This is args /connect <ip> <port> <your_nickname>
        ### NOTICE: It would be better to connect first then set your IP to a certain nickname. Or easily,
        ### just args /connect <ip> <port> and just split the /nickname functionality

            else:
                message_box.insert(tk.END, "Invalid /connect command. Usage: /connect <ip> <port> <optional: nickname>\n")

            ### We can change this else part.
        elif message.startswith("/nick"):
            if self.is_connected:
                message_box.insert(tk.END, "You can't set a nickname while connected!\n")
            else:
                nick_args = message.split()
                if len(nick_args) == 2:
                    self.nick = nick_args[1]
                    if self.is_connected:
                        self.disconnect_from_peer(self.peer_ip, int(self.peer_port))
                        self.connect_to_peer(self.peer_ip, int(self.peer_port))
                    message_box.insert(tk.END, f"Nickname set to {self.nick}\n")
                else:
                    message_box.insert(tk.END, "Invalid /nick command. Usage: /nick <nickname>\n")
        elif message == "/peers":
            self.display_peers()

        ### This displays peers that are DIRECTLY CONNECTED. If we insert a DHT table, we can:
        ### Find DIRECTLYCONNECTED peers and INDIRECTLYCONNECTED peers (through BFS)
        ### BFS should be administered to the DHT instead.

        elif message.startswith("/disconnect"):
            # disconnect_args = message.split()
            # if len(disconnect_args) == 3:
            #     receiver_ip = disconnect_args[1]
            #     receiver_port = int(disconnect_args[2])
            self.disconnect_from_peer(self.peer_ip, self.peer_port)
            # else:
            #     message_box.insert(tk.END, "Invalid /disconnect command. Usage: /disconnect <ip> <port>\n")

        ### This is to handle disconnections.
        elif message.startswith("/port"):
            port_args = message.split()
            if len(port_args) == 2:
                self.receiver_port = int(port_args[1])
                if self.is_connected:
                    self.disconnect_from_peer(self.peer_ip, self.peer_port)
                message_box.insert(tk.END, f"Changed port to: {self.receiver_port}\n")
                print(f"Changed port to: {self.receiver_port}\n")
            else:
                message_box.insert(tk.END, "Invalid /port command. Usage: /port <port>\n")
        else:
            if not message.startswith("\b/init"):
                print(message)
            send_thread = threading.Thread(target=self.send_message_thread, args=(message,))
            send_thread.start()

        ### If there were no slash (/) commands, it will act as a message box nalang.

    def connect_to_peer(self, peer_ip, peer_port):
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ### conn = to establish TCP connection (TCP socket)
            conn.connect((peer_ip, peer_port))
            ### .connect() to establish a connection for the tuple IP and port.
            conn.send(f"\b/init {self.receiver_ip} {self.receiver_port} {self.nick}".encode())
            ### Simple appending of tuple. So IP-Port-Nickname
            # message_box.insert(tk.END, f"Connected to {self.peer_nick} ({self.peer_ip}:{self.peer_port})\n")
            ### We can disregard the IP and Receiver port if nickname != ""
            receive_thread = threading.Thread(target=self.receive_messages, args=(conn, self.peer_nick))
            ### Multithreading, to receive messages.
            receive_thread.start()
            if len(connected_peers) == 0:
                connected_peers.append((self.peer_ip, self.peer_port, self.peer_nick))
            elif connected_peers[::-1][0] != (self.peer_ip, self.peer_port, self.peer_nick): 
                connected_peers.append((self.peer_ip, self.peer_port, self.peer_nick))
            ### Initialization of multithread.
            self.is_connected = True

        except Exception as e:
            error_message = f"Failed to connect to {self.peer_nick} ({self.peer_ip}:{self.peer_port}): {str(e)}"
            message_box.insert(tk.END, error_message + "\n")

            ### Error Handling
    
    def handle_init(self, init):
        init = init.decode()
        if init.startswith("\b/init"):
            init = init[2:].split(" ")
            self.peer_ip = init[1]
            self.peer_port = init[2]
            self.peer_nick = init[3]
    def disconnect_from_peer(self, receiver_ip, receiver_port):
        try:
            for peer in connected_peers:
                ip, port, _ = peer
                if ip == receiver_ip and port == receiver_port:
                    connected_peer = peer
                    break
            ### FIFO pala siya. Naka FIFO to get the first person sa list Tapos yun ang ididisconnect.

            if connected_peers:
                nickname = connected_peers[2]
                connected_peers.pop(0)
                message_box.insert(tk.END, f"Disconnected from {nickname} ({receiver_ip}:{receiver_port})\n")
                self.is_connected = False
                self.display_peers()
            else:
                message_box.insert(tk.END, f"Not connected to {receiver_ip}:{receiver_port}\n")

            ### Disconnection is made only to those who are connected DIRECTLY.

        except Exception as e:
            error_message = f"Failed to disconnect from {receiver_ip}:{receiver_port}: {str(e)}"
            message_box.insert(tk.END, error_message + "\n")
            ### Error Handlingf

    def send_message_thread(self, message):
        ### This function updates the thread. Only if the sent message is for all.
        try:
            for peer in connected_peers:
                print(peer)
                print(message)
                peer_ip, peer_port, _ = peer
                send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                send_socket.connect((peer_ip, int(peer_port)))
                send_socket.sendall(message.encode())
                send_socket.close()

            if message.startswith("/"):
                sent_messages.append(f"Command sent: {message}")
                message_box.insert(tk.END, f"Command sent: {message}\n")
            else:
                sent_messages.append(f"Sent message to peers: {message}")
                message_box.insert(tk.END, f"Sent message to peers: {message}\n")
        except Exception as e:
            print("error", message)
            error_message = f"Failed to send message: {e}"
            message_box.insert(tk.END, error_message + "\n")

    def listen_thread(self):
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.bind((self.receiver_ip, self.receiver_port))
        listen_socket.listen(3)
        if not self.is_connected:
            while True:
                conn, address = listen_socket.accept()
                if not self.is_connected:
                    data = conn.recv(4096)
                    self.handle_init(data)
                    self.connect_to_peer(self.peer_ip, int(self.peer_port))
                    self.is_connected = True
                    conn.send(f"\b/init {self.receiver_ip} {self.receiver_port} {self.nick}".encode())
                    message_box.insert(tk.END, f"{self.peer_ip}:{self.peer_port} ({self.peer_nick}) has joined the chat.\n")
                    # connected_peers.append((self.peer_ip, self.peer_port, self.peer_nick))
                    if self.nick == "Anon":
                        message_box.insert(tk.END, "We noticed you don't have a nickname. Set one now via /nick <nickname>.\n")
                    
                receive_thread = threading.Thread(target=self.receive_messages, args=(conn, address))
                receive_thread.start()
    def receive_messages(self, conn, address):
        while True:
            try:
                data = conn.recv(4096)
                ### This is to convert the received things to bytes. 4096 is the size.
                if data:    
                    received_message = data.decode() ### Decoding of bytes
                    received_messages.append(received_message) ### Received message is then used to be printed into the message box

                    if not received_message.startswith("\b/init"): message_box.insert(tk.END, f"Message received from {self.peer_ip}:{self.peer_port} ({self.peer_nick}): {received_message}\n")
                else:
                    break

            except Exception as e:
                error_message = f"Failed to receive message from {self.peer_ip}:{self.peer_port} ({self.peer_nick}): {str(e)}\n"
                message_box.insert(tk.END, error_message + "\n")
                break

    # def update_peers(self):
    #     ### The Display peers shows a separate box with "Connected Peers" to be shown. Medyo redundant.
    #     peers_text = "Connected Peers:\n"
    #     for peer in connected_peers:
    #         ip, port, nickname = peer
    #         peers_text += f"{ip}:{port} ({nickname})\n"
    #     peers_text += "\n"

    #     peers_box.configure(state="normal")
    #     peers_box.delete("1.0", tk.END)
    #     peers_box.insert(tk.END, peers_text)
    #     peers_box.configure(state="disabled")

    def display_peers(self):
        if len(connected_peers) != 0:
            message_box.insert(tk.END, "----------------------\n")
            message_box.insert(tk.END, "Connected Peers:\n")
            message_box.insert(tk.END, "----------------------\n")
            count = 1
            for peer in connected_peers:
                peer_ip, peer_port, peer_nick = peer
                message_box.insert(tk.END, f"({count}) {peer_ip}:{peer_port} ({peer_nick})\n")
        else:
            message_box.insert(tk.END, "You have no connected peers.\n")
        # message_box.window_create(tk.END, window=peers_box)
        # message_box.insert(tk.END, "\n")

### The code for below is to setup the Tkinter interface.
window = tk.Tk()
window.minsize(800, 650)
window.title("Fire P2P Chat")
chat = ChatApp()
window.bind('<Return>', chat.send_message)
local_ip = client.get_local_ip()
receive_port = client.get_free_port()
chat.receiver_port = receive_port
chat.receiver_ip = local_ip

connected_peers = []

message_label = tk.Label(window, text="Chat Room", font=("Helvetica", 21, "bold"))
message_label.grid(row=0, column=0,)
received_messages = []
sent_messages = []


message_box = tk.Text(window, font=("Helvetica", 14))
message_box.grid(row=1, column=0, sticky='nsew',padx=10,pady=(15,0))

message_box.insert(tk.END, f"Your IP Address: {chat.receiver_ip}\n")
message_box.insert(tk.END, f"Listening at Port {chat.receiver_port}\n")
message_box.insert(tk.END, f"You don't have a nick! Set one now via /nick <nickname> or you will be called Anon.\n")
peers_box = tk.Text(window, height=6, width=30)
peers_box.configure(state="disabled")

message_entry = tk.Entry(window, font=("Helvetica", 14))
message_entry.grid(row=2, column=0, sticky='nsew',padx=10,pady=15)

send_button = tk.Button(window, text="Send", command=chat.send_message, font=("Helvetica", 8, "bold"), height=1)
send_button.grid(row=2, column=1, sticky='nsew', padx=10)

window.grid_columnconfigure(0, weight=1)
window.grid_rowconfigure((0,1), weight=1)

listen_thread = threading.Thread(target=chat.listen_thread)
listen_thread.start()
window.mainloop()
