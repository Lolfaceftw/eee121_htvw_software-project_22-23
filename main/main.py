import socket
# Socket for networking
import tkinter as tk
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
        self.nick = None
    def send_message(self, event = None):
        message = message_entry.get()
        ### Message_entry.get() was used to retrieve what has been entered on the message box.


        if message.startswith("/connect"):
            connect_args = message.split()
            if len(connect_args) == 4:
                self.receiver_ip = connect_args[1]
                self.receiver_port = int(connect_args[2])
                self.nick = connect_args[3]
                self.connect_to_peer(self.receiver_ip, self.receiver_port, self.nick)

        ### checking for the command. /connect. This is args /connect <ip> <port> <your_nickname>
        ### NOTICE: It would be better to connect first then set your IP to a certain nickname. Or easily,
        ### just args /connect <ip> <port> and just split the /nickname functionality

            else:
                message_box.insert(tk.END, "Invalid /connect command. Usage: /connect <ip> <port> <nickname>\n")

            ### We can change this else part.

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
            self.disconnect_from_peer(self.receiver_ip, self.receiver_port)
            # else:
            #     message_box.insert(tk.END, "Invalid /disconnect command. Usage: /disconnect <ip> <port>\n")

        ### This is to handle disconnections.
        elif message.startswith("/port"):
            port_args = message.split()
            if len(port_args) == 2:
                self.receiver_port = int(port_args[1])
                if self.is_connected:
                    self.disconnect_from_peer(self.receiver_ip, self.receiver_port)
                message_box.insert(tk.END, f"Changed port to: {self.receiver_port}\n")
                print(f"Changed port to: {self.receiver_port}\n")
            else:
                message_box.insert(tk.END, "Invalid /port command. Usage: /port <port>\n")
        else:
            send_thread = threading.Thread(target=self.send_message_thread, args=(message,))
            send_thread.start()

        ### If there were no slash (/) commands, it will act as a message box nalang.

    def connect_to_peer(self, receiver_ip, receiver_port, nickname):
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ### conn = to establish TCP connection (TCP socket)
            conn.connect((receiver_ip, receiver_port))
            ### .connect() to establish a connection for the tuple IP and port.
            connected_peers.append((receiver_ip, receiver_port, nickname))
            ### Simple appending of tuple. So IP-Port-Nickname
            message_box.insert(tk.END, f"Connected to {nickname} ({receiver_ip}:{receiver_port})\n")
            ### We can disregard the IP and Receiver port if nickname != ""
            self.update_peers()
            receive_thread = threading.Thread(target=self.receive_messages, args=(conn, nickname))
            ### Multithreading, to receive messages.
            receive_thread.start()
            ### Initialization of multithread.
            self.is_connected = True

        except Exception as e:
            error_message = f"Failed to connect to {nickname} ({receiver_ip}:{receiver_port}): {str(e)}"
            message_box.insert(tk.END, error_message + "\n")

            ### Error Handling

    def disconnect_from_peer(self, receiver_ip, receiver_port):
        try:
            connected_peer = None
            for peer in connected_peers:
                ip, port, _ = peer
                if ip == receiver_ip and port == receiver_port:
                    connected_peer = peer
                    break
            ### FIFO pala siya. Naka FIFO to get the first person sa list Tapos yun ang ididisconnect.

            if connected_peer:
                nickname = connected_peer[2]
                connected_peers.remove(connected_peer)
                message_box.insert(tk.END, f"Disconnected from {nickname} ({receiver_ip}:{receiver_port})\n")
                self.is_connected = False
                self.update_peers()
            else:
                message_box.insert(tk.END, f"Not connected to {receiver_ip}:{receiver_port}\n")

            ### Disconnection is made only to those who are connected DIRECTLY.

        except Exception as e:
            error_message = f"Failed to disconnect from {receiver_ip}:{receiver_port}: {str(e)}"
            message_box.insert(tk.END, error_message + "\n")
            ### Error Handling

    def send_message_thread(self, message):
        ### This function updates the thread. Only if the sent message is for all.
        try:
            for peer in connected_peers:
                receiver_ip, receiver_port, _ = peer
                send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                send_socket.connect((receiver_ip, receiver_port))
                send_socket.sendall(message.encode())
                send_socket.close()

            sent_messages.append(f"Sent message to peers: {message}")
            message_box.insert(tk.END, f"Sent message to peers: {message}\n")
        except Exception as e:
            error_message = f"Failed to send message: {str(e)}"
            message_box.insert(tk.END, error_message + "\n")

    def listen_thread(self):
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.bind((self.receiver_ip, self.receiver_port))
        listen_socket.listen(3)
        
        while True:
            conn, address = listen_socket.accept()
            receive_thread = threading.Thread(target=self.receive_messages, args=(conn, address))
            receive_thread.start()
    def receive_messages(self, conn, address, nickname = "Unknown"):
        while True:
            try:
                data = conn.recv(4096)
                ### This is to convert the received things to bytes. 4096 is the size.
                if data:
                    received_message = data.decode() ### Decoding of bytes
                    received_messages.append(received_message) ### Received message is then used to be printed into the message box
                    message_box.insert(tk.END, f"Message received from {address[0]}:{address[1]} ({nickname}): {received_message}\n")
                else:
                    break

            except Exception as e:
                error_message = f"Failed to receive message from {address[0]}:{address[1]} ({nickname}): {str(e)}"
                message_box.insert(tk.END, error_message + "\n")
                break

    def update_peers(self):
        ### The Display peers shows a separate box with "Connected Peers" to be shown. Medyo redundant.
        peers_text = "Connected Peers:\n"
        for peer in connected_peers:
            ip, port, nickname = peer
            peers_text += f"{ip}:{port} ({nickname})\n"
        peers_text += "\n"

        peers_box.configure(state="normal")
        peers_box.delete("1.0", tk.END)
        peers_box.insert(tk.END, peers_text)
        peers_box.configure(state="disabled")

    def display_peers(self):
        self.update_peers()
        message_box.insert(tk.END, "----------------------\n")
        message_box.insert(tk.END, "Connected Peers:\n")
        message_box.insert(tk.END, "----------------------\n")
        message_box.window_create(tk.END, window=peers_box)
        message_box.insert(tk.END, "\n")


### The code for below is to setup the Tkinter interface.
window = tk.Tk()
chat = ChatApp()
window.bind('<Return>', chat.send_message)
local_ip = client.get_local_ip()
receive_port = client.get_free_port()
chat.receiver_port = receive_port
chat.receiver_ip = local_ip

connected_peers = []

message_label = tk.Label(window, text="Message:")
message_label.pack()
message_entry = tk.Entry(window)
message_entry.pack()

send_button = tk.Button(window, text="Send", command=chat.send_message)
send_button.pack()

received_messages = []
sent_messages = []

message_box = tk.Text(window)
message_box.pack()
message_box.insert(tk.END, f"Your IP Address: {chat.receiver_ip}\n")
message_box.insert(tk.END, f"Listening at Port {chat.receiver_port}\n")
peers_box = tk.Text(window, height=6, width=30)
peers_box.configure(state="disabled")

listen_thread = threading.Thread(target=chat.listen_thread)
listen_thread.start()
window.mainloop()
