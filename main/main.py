import socket
# Socket for networking
import tkinter as tk
from tkinter import ttk
# Tkinter used as interface
import threading
# Threading used for multithreading
from lib.client import Client as client
import pickle

class ChatApp:
    def __init__(self) -> None:
        super(ChatApp, self).__init__()
        #! Experimental: The boolean still has no apparent use, at least in this version.
        self.is_connected = False

        # Your local IP, local port, and local nick.
        self.receiver_ip = None
        self.receiver_port = None
        self.nick = "Anon"

        # The peer's IP, port, and nick. Note: This will continuously change as you receive messages from different peers.
        self.peer_ip = None
        self.peer_port = None
        self.peer_nick = None

        # The client's received message. Default: "No message."
        self.recvd_message = "No message."

    def send_message(self, event = None) -> None:
        """
        Send message function to grab the event in the message box. 

        Args:
            event: Captures the <Return> key for sending the message. Defaults to None.
        """
        
        # Get the message entry in the tkinter text box.
        message = message_entry.get()

        #* Automatically deletes the text in message_entry after sending.
        message_entry.delete(0, tk.END)

        # Do not send a message when it is empty or contains spaces.
        if message.isspace() or len(message) == 0:
            message_box.insert(tk.END, "Please enter a message.\n")

        # /connect <peer_ip> <peer_port> <local_nick>. Connects to the peer with your nickname.
        elif message.startswith("/connect"):
            connect_args = message.split()

            if len(connect_args) >= 3:
                self.peer_ip = connect_args[1]
                self.peer_port = int(connect_args[2])
                if len(connect_args) == 4:
                    self.nick = connect_args[3]
                self.connect_to_peer(self.peer_ip, int(self.peer_port))

            else:
                message_box.insert(tk.END, "Invalid /connect command. Usage: /connect <ip> <port> <optional: nickname>\n")

        # /nick <nick>. Change your local nickname.
        #* Note: This works best if the peer will set a nickname before being connected to.
        #TODO: Change nickname while connected. Possible if we fix /disconnect and reconnect back with the new nickname.
        elif message.startswith("/nick"):
            if self.is_connected:
                message_box.insert(tk.END, "You can't set a nickname while connected!\n")

            else:
                nick_args = message.split()
                if len(nick_args) == 2:
                    self.nick = nick_args[1]

                    #! Experimental since self.disconnect_from_peer() still doesn't work well.
                    if self.is_connected:
                        self.disconnect_from_peer(self.peer_ip, int(self.peer_port))
                        self.connect_to_peer(self.peer_ip, int(self.peer_port))

                    message_box.insert(tk.END, f"Nickname set to {self.nick}\n")
                else:
                    message_box.insert(tk.END, "Invalid /nick command. Usage: /nick <nickname>\n")

        #! Work in progress. P2P network is still buggy.
        #TODO: Send and receive information about each peer's connected_peers.
        # 1. When a peer is added to the network, the peer must also send its own directly connected peers to all the network.
        # 2. In return, for each client, they will also send their own connected peers for each peer in the network.
        # 3. The final peer network shall combine all the connected peers of each peer in the network.
        elif message == "/peers":
            self.display_peers()

        #/disconnect <peer_ip> <peer_port>. Disconnects to the peer
        #! Not working after changes in mechanism of app.
        #TODO: Disconnect from all peers in the network.
        # 1. Once the disconnect command is sent, the client should attempt to disconnect to each peer in the network. For simplicity, we can start with directly connected peers and if that works, we can proceed to code for all peers in the network.
        # 2. Sockets must be closed to prevent further issues in reconnecting.
        # 3. Send a disconnect comment to the sockets of each peer so the peers will also disconnect from the client.
        #* 4. Since it will disconnect from all peers, I think we should omit the arguments required from self.disconnect_from_peer() and instead refer to the directly/indirectly connected peers.
        elif message.startswith("/disconnect"):
            self.disconnect_from_peer(self.peer_ip, self.peer_port)


        #/port <port>. Change the port of the client.
        #! Still buggy since it needs to make use of the self.disconnect_from_peer().
        #TODO: Fix the disconnect function and make sure restarting is smooth.
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

        # Starts the message thread if it is not a command.
        else:
            # For debugging purposes, this will just print the message in the terminal as long as it's not /init.
            if not message.startswith("\b/init"):
                print(message)
            # Starts the message thread.
            send_thread = threading.Thread(target=self.send_message_thread, args=(message,))
            send_thread.start()

    def connect_to_peer(self, peer_ip, peer_port):
        """
        Connects to a peer in the local area network.

        Args:
            peer_ip (string): The peer ip to connect to. This must be connected under the same wifi.
            peer_port (string): The peer port to connect to. This must be in listening mode.
        """
        try:
            # Create a socket and connect to the peer.
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((peer_ip, peer_port))

            #? This part of the code is an inefficient fix for a bug I found. Without this snippet, the peer will be appended two times: one with its None nick, and the other is the updated "Anon" nick. 
            #* If you have a more efficient fix for this, it would be great.
            if self.peer_nick is not None:
                # Automatically append if there are no peers connected.
                if len(connected_peers) == 0:
                    connected_peers.append((self.peer_ip, self.peer_port, self.peer_nick))
                # Prevent duplicates.
                elif connected_peers[::-1][0] != (self.peer_ip, self.peer_port, self.peer_nick): 
                    connected_peers.append((self.peer_ip, self.peer_port, self.peer_nick))

            # Send information about the peer about the client's local ip, port, nick, and connected peers.
            conn.send(f"\b/init-{self.receiver_ip}-{self.receiver_port}-{self.nick}-{self.connected_peers}".encode())
            self.is_connected = True

        # Catch error handling.
        except Exception as e:
            error_message = f"Failed to connect to {self.peer_nick} ({self.peer_ip}:{self.peer_port}): {str(e)}"
            message_box.insert(tk.END, error_message + "\n")

    def handle_init(self, init):
        """
        Handles initial information received from the peer. This is usually hidden from the chatbox.
        
        Args:
            init (byte): The data received from the peer.
        """
        # Decodes from type byte to type string.
        init = init.decode()

        # If it starts with \b/init, acquire the information.
        #* This is a crucial functionality to determine the information about the peer.
        if init.startswith("\b/init"):
            init = init[2:].split("-")
            self.peer_ip = init[1]
            self.peer_port = init[2]
            self.peer_nick = init[3]
            self.recvd_message = init[5:]

            #! Still experimental.
            p2p_network.append(eval(init[4]))

    #! Not Working. To repeat:
    #TODO: Disconnect from all peers in the network.
    # 1. Once the disconnect command is sent, the client should attempt to disconnect to each peer in the network. For simplicity, we can start with directly connected peers and if that works, we can proceed to code for all peers in the network.
    # 2. Sockets must be closed to prevent further issues in reconnecting.
    # 3. Send a disconnect comment to the sockets of each peer so the peers will also disconnect from the client.
    #* 4. Since it will disconnect from all peers, I think we should omit the arguments required from self.disconnect_from_peer() and instead refer to the directly/indirectly connected peers.
    def disconnect_from_peer(self, receiver_ip, receiver_port):
        try:
            for peer in connected_peers:
                ip, port, _ = peer
                if ip == receiver_ip and port == receiver_port:
                    connected_peer = peer
                    break

            if connected_peers:
                nickname = connected_peers[2]
                connected_peers.pop(0)
                message_box.insert(tk.END, f"Disconnected from {nickname} ({receiver_ip}:{receiver_port})\n")
                self.is_connected = False
                self.display_peers()
            else:
                message_box.insert(tk.END, f"Not connected to {receiver_ip}:{receiver_port}\n")

        except Exception as e:
            error_message = f"Failed to disconnect from {receiver_ip}:{receiver_port}: {str(e)}"
            message_box.insert(tk.END, error_message + "\n")
            
    def send_message_thread(self, message):
        """
        Main thread for sending messages.
        Args:
            message (string): The main message to send.
        """

        #TODO: Send the message for all indirect peers in the network. For now, it can only send to directly connected peers.
        try:
            for peer in connected_peers:
                peer_ip, peer_port, _ = peer
                # Create a socket to send.
                send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                send_socket.connect((peer_ip, int(peer_port)))
                # Sends to all peers in the socket the information about the client and the message that it sent.
                send_socket.sendall(f"\b/init-{self.receiver_ip}-{self.receiver_port}-{self.nick}-{self.connected_peers}-{message}".encode())
                # Close the socket.
                send_socket.close()

            # Handles whether a message or command was sent.
            if message.startswith("/"):
                sent_messages.append(f"Command sent: {message}")
                message_box.insert(tk.END, f"Command sent: {message}\n")
                message_box.see(tk.END)

            else:
                sent_messages.append(f"Sent message to peers: {message}")
                message_box.insert(tk.END, f"Sent message to peers: {message}\n")
                message_box.see(tk.END)
                
        # Catch exception.
        except Exception as e:
            print("error", message)
            error_message = f"Failed to send message: {e}"
            message_box.insert(tk.END, error_message + "\n")

    def listen_thread(self):
        """
        Main listen thread that waits for data for incoming connections in the P2P network.
        """
        # Establish a socket to listen from.
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.bind((self.receiver_ip, self.receiver_port))
        listen_socket.listen(3)

        while True:
            # Wait for data.
            conn, address = listen_socket.accept()
            data = conn.recv(4096)

            # Once there is data (bytes), decode and receive the message.
            if data:
                # Handle the information and see from what peer is it from and what is its message.
                self.handle_init(data)

                # If the peer is not in the connected list, append it and print out it has joined the chat.
                if (self.peer_ip, self.peer_port, self.peer_nick) not in connected_peers:
                    self.connect_to_peer(self.peer_ip, int(self.peer_port))
                    message_box.insert(tk.END, f"{self.peer_ip}:{self.peer_port} ({self.peer_nick}) has joined the chat.\n")

                    # Remind the user to set a nickname if it's Anon.
                    #! This will constantly be printed out in the client for each new connection made. 
                    #! Still won't work because it requires the self.disconnect() function to operate. Client needs to reconnect.
                    if self.nick == "Anon":
                        message_box.insert(tk.END, "We noticed you don't have a nickname. Set one now via /nick <nickname>.\n")

                self.is_connected = True
                # Once data has been received, send to the peer the client's own information.
                conn.send(f"\b/init-{self.receiver_ip}-{self.receiver_port}-{self.nick}-{connected_peers}".encode())

                # Append the messages.
                if len(self.recvd_message) >0:
                    received_message = " ".join(self.recvd_message)
                    received_messages.append(received_message) #
    
                if len(self.recvd_message) != 0: 
                    message_box.insert(tk.END, f"Message received from {self.peer_ip}:{self.peer_port} ({self.peer_nick}): {received_message}\n")
                    message_box.see(tk.END)

    def display_peers(self):
        """
        Displays all the directly peers and all the peers in the network.
        """
        if len(connected_peers) != 0:
            message_box.insert(tk.END, "----------------------\n")
            message_box.insert(tk.END, "Directly Connected Peers:\n")
            message_box.insert(tk.END, "----------------------\n")
            for index in range(len(connected_peers)):
                peer_ip, peer_port, peer_nick = connected_peers[index][0], connected_peers[index][1],connected_peers[index][2]
                message_box.insert(tk.END, f"({index + 1}) {peer_ip}:{peer_port} ({peer_nick})\n")
            #! Work in progress.
            #TODO: Send and receive information about each peer's connected_peers.
            # 1. When a peer is added to the network, the peer must also send its own directly connected peers to all the network.
            # 2. In return, for each client, they will also send their own connected peers for each peer in the network.
            # 3. The final peer network shall combine all the connected peers of each peer in the network.
            message_box.insert(tk.END, "----------------------\n")
            message_box.insert(tk.END, "P2P Network:\n")
            message_box.insert(tk.END, "----------------------\n")
            message_box.insert(tk.END, p2p_network)
        else:
            message_box.insert(tk.END, "You have no connected peers.\n")

    #! Moved this function inside the listen thread.
    # def receive_messages(self, conn, address):
    #     while True:
    #         try:
    #             data = conn.recv(4096)
    #             ### This is to convert the received things to bytes. 4096 is the size.
    #             if data:    
    #                 received_message = data.decode() ### Decoding of bytes
    #                 received_messages.append(received_message) ### Received message is then used to be printed into the message box
                    
    #                 if not received_message.startswith("\b/init"): message_box.insert(tk.END, f"Message received from {self.peer_ip}:{self.peer_port} ({self.peer_nick}): {received_message}\n")
    #             else:
    #                 break

    #         except Exception as e:
    #             error_message = f"Failed to receive message from {self.peer_ip}:{self.peer_port} ({self.peer_nick}): {str(e)}\n"
    #             message_box.insert(tk.END, error_message + "\n")
                

if __name__ == '__main__':
    # Initialize root window.
    window = tk.Tk()

    # Instantiate the ChatApp class.
    chat = ChatApp()

    # Minimum size should be 800x650 for readability.
    window.minsize(800, 650)

    # Can choose whatever title you want for the window.
    window.title("Fire P2P Chat")

    # Binds the return key for sending a message.
    window.bind('<Return>', chat.send_message)

    # Set up the necessary local ip and ports.
    local_ip = client.get_local_ip()
    receive_port = client.get_free_port()
    chat.receiver_port = receive_port
    chat.receiver_ip = local_ip

    # Global variables.
    connected_peers = []
    p2p_network = []
    received_messages = []
    sent_messages = []

    #* WIDGETS
    # Headline for the chatroom.
    message_label = tk.Label(window, text="Chat Room", font=("Helvetica", 21, "bold"))
    message_label.grid(row=0, column=0,)

    # Main chat box area.
    message_box = tk.Text(window, font=("Helvetica", 14))
    message_box.see(tk.END)
    message_box.grid(row=1, column=0, sticky='nsew',padx=10,pady=(15,0))

    # Send initial information about the client.
    message_box.insert(tk.END, f"Your IP Address: {chat.receiver_ip}\n")
    message_box.insert(tk.END, f"Listening at Port {chat.receiver_port}\n")
    message_box.insert(tk.END, f"You don't have a nick! Set one now via /nick <nickname> or you will be called Anon.\n")

    #? Honestly don't know the reasoning for this.
    peers_box = tk.Text(window, height=6, width=30)
    peers_box.configure(state="disabled")

    # Message box.
    message_entry = tk.Entry(window, font=("Helvetica", 14))
    message_entry.grid(row=2, column=0, sticky='nsew',padx=10,pady=15)

    # Send button.
    send_button = tk.Button(window, text="Send", command=chat.send_message, font=("Helvetica", 8, "bold"), height=1)
    send_button.grid(row=2, column=1, sticky='nsew', padx=10)

    # Configuration to automatically resize the widgets.
    window.grid_columnconfigure(0, weight=1)
    window.grid_rowconfigure((0,1), weight=1)

    # Start the listening thread for incoming connections.
    listen_thread = threading.Thread(target=chat.listen_thread)
    listen_thread.start()

    # Loop through the window.
    window.mainloop()
