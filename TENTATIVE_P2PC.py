from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname
from threading import Thread
from tkinter import messagebox, scrolledtext, ttk
from tkinter.messagebox import askyesno
import tkinter as tk
import sys

class Peer:
    def __init__(self, u_host, u_port: int, alias: str=''):
        self.host = u_host
        self.port = u_port
        self.alias = alias
        self.u_socket = socket(AF_INET, SOCK_STREAM)
        self.routing_table = {} # dict{alias : tuple(latency, hop)}
        self.peer_aliases = {} # dict{socket : alias}
        self.direct_connects = [] # list ((ip1,ip2),latency)
        self.table = []
        self.connected = False
        # start GUI Thread
        Thread(target=self.gui).start()

    def init_info(self):
        self.show_message(f"Welcome, {self.alias}! Your client's ip address is {self.host}\n")
        self.show_message(f"Listening at Port {self.port}\n")
        self.show_message(f"Connect to a peer now using the panel on the right!\n")
        self.show_message("For a list of commands, use /help\n")

    def receive_data(self, client_socket: socket, once=False):
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            command, info = data.split(' ', 1)

            #* gMSG is for group messages
            #* Sending of messages to all available peers and showing them.
            if command == 'gMSG':
                from_peer, msg = info.split(' ', 1)
                for peersock in self.peer_aliases:
                    if self.peer_aliases[peersock] != self.peer_aliases[client_socket]:
                        self.send_data(data, peersock)
                self.show_message(f'[{from_peer}] {msg}')

            #* priv_msg is for the /pm functionality.
            #* Since there are unavailable peer-to-socket in self.peer_aliases, it is sent to all instead.
            #* And once sent to all, if the receiver is match, then it only displays the message.
            
            #? This can be changed pa. 
            elif command == "priv_msg":
                from_peer, receiver, msg = info.split(' ', 2)
                for peersock in self.peer_aliases:
                    if self.peer_aliases[peersock] != self.peer_aliases[client_socket]:
                        self.send_data(data, peersock)
                if self.alias == receiver:
                    self.show_message(f'[{from_peer} whispered to You] {msg}')

            #* WHOAMI is set by Cnyl. This is to show the name ig.
            elif command == 'WHOAMI':
                alias, latency = info.split(' ',1)
                self.peer_aliases[client_socket] = alias
                if latency == 'to_set':
                    break
                self.routing_table[alias] = (int(latency),alias) 
                if once:
                    break

            #* Associated with the /connect functionality. 
            elif command == "connect":
                sender, receiver, w_latency = info.split(' ', maxsplit=2)
                if self.alias == receiver:
                    pair = (self.alias, sender)
                    self.direct_connects = [x for x in self.direct_connects if x[0] != pair]  
                    self.direct_connects.append((pair, w_latency))

                for peersock in self.peer_aliases:
                    if self.peer_aliases[peersock] != self.peer_aliases[client_socket]:
                        self.send_data(data, peersock)

            #! THIS CODE IS USED FOR TROUBLESHOOTING
            elif command == "printall":
                print(self.direct_connects)
                print(self.u_socket)
                print(self.peer_aliases)

            #! THIS CODE IS USED FOR ASSIGNING DIRECT CONNECTIONS
            elif command == "direct_connect":
                transmitter, receiver, weight= info.split(' ')
                d_connected_pair = (receiver, transmitter)
                direct_connection = (d_connected_pair, int(weight))
                self.direct_connects.append(direct_connection)

            #* Code used for routing table
            elif command == "RT":
                table = info.split()
                modif_table = {}
                from_peer = ''
                for row in table:
                    alias, latency = row.split('-', 1)
                    modif_table[alias] = int(latency)
                    if latency == '0':
                        from_peer += alias

                distance = modif_table[self.alias]
                for peer in self.routing_table:
                    if peer in modif_table:
                        if self.routing_table[peer][0] > modif_table[peer] + distance:
                            self.routing_table[peer] = (modif_table[peer] + distance, from_peer)
                    elif peer != self.alias:
                        self.routing_table[peer] = from_peer

                for peer in modif_table:
                    if peer not in self.routing_table:
                        self.routing_table[peer] = (modif_table[peer] + distance, from_peer)

            #* For the /disconnect functionality. This allows the user to disconnect from the network and send a disconnection notice.
            #* Also, the online user list is updated.
            elif command == "disconnect":
                for peersock in self.peer_aliases:
                    print(self.peer_aliases[peersock])
                    if self.peer_aliases[peersock] != self.peer_aliases[client_socket]:
                        self.send_data(data, peersock)

                for alias in self.peer_aliases:
                    if self.peer_aliases[alias] == info:
                        del self.peer_aliases[alias]
                        break
                del self.routing_table[info]

                for connection_d in self.direct_connects:
                    if connection_d[0] == (self.alias, info):
                        self.direct_connects.pop(self.direct_connects.index(connection_d))
                self.show_message(f'{info} left the server.\n')
                self.show_activepeers()

                
            #* Changes the nickname of the user and informs the whole network.
            #* This also updates the user list.
            elif command == "nickname":
                info = info.split(' ')
                info[1] = info[1][:-1]
                self.routing_table[info[1]] = self.routing_table.pop(info[0])
                
                for names in self.peer_aliases:
                    if self.peer_aliases[names] == info[0]:
                        self.peer_aliases[names] = info[1]
                        
                for connection in self.direct_connects:
                    if connection[0][0] == info[0]:
                        self.direct_connects.append(((info[1],connection[0][1]),connection[1]))
                        self.direct_connects.pop(self.direct_connects.index(connection))
                    elif connection[0][1] == info[0]:
                        self.direct_connects.append(((connection[0][0],info[1]),connection[1]))
                        self.direct_connects.pop(self.direct_connects.index(connection))

                self.show_activepeers()

                for peersock in self.peer_aliases:
                    if self.peer_aliases[peersock] != self.peer_aliases[client_socket]:
                        self.send_data(data, peersock)

            #! USED FOR RT UPDATE
            elif command == "update_RT":
                sender, new_peer, latency = info.split()
                self.show_message(f'{new_peer} has joined the server!\n')
                if not self.connected: self.connected = True
                if new_peer not in self.routing_table:
                    distance = self.routing_table[sender][0] + int(latency)
                    self.routing_table[new_peer] = (distance, sender)
                
                for peersock in self.peer_aliases:
                    if self.peer_aliases[peersock] != sender:
                        self.send_data(f'update_RT {self.alias} {new_peer} {self.routing_table[sender][0] + int(latency)}',peersock)

                self.show_activepeers()
                
    def change_nickname(self, name):
        self.routing_table[name] = self.routing_table.pop(self.alias)
                
        for names in self.peer_aliases:
            if self.peer_aliases[names] == self.alias:
                self.peer_aliases[names] = name
                
        for connection in self.direct_connects:
            if connection[0][0] == self.alias:
                self.direct_connects.append(((name,connection[0][1]),connection[1]))
            elif connection[0][1] == self.alias:
                self.direct_connects.append(((connection[0][0],name),connection[1]))
            self.direct_connects.pop(self.direct_connects.index(connection))

        self.alias = name
        self.show_activepeers()
        
    def send_data(self, data: str, peer_socket):
        try:
            peer_socket.send(data.encode('utf-8'))
        except:
            print("You send to a non-existing peer")

    def update_RT(self, alias, through_alias):
        for peersock in self.peer_aliases:
            peer_alias = self.peer_aliases[peersock]
            if peer_alias in self.routing_table.values():
                self.send_data(f'{alias} has joined the server!', peersock)
    
    def broadcast(self, data):
        for peer in self.peer_aliases:
            self.send_data(data, peer)
        
    def allow_connection(self):
        try:
            self.u_socket.bind((self.host, self.port))
            self.u_socket.listen(5)
            self.routing_table[self.alias] = (0,'none')
        except Exception as e:
            self.show_message(str(e) + "\n")

        while True:
            clientsock, clientaddr = self.u_socket.accept()
            self.peer_aliases[clientsock] = clientaddr
            
            # sends alias 
            self.send_data(f'WHOAMI {self.alias} to_set', clientsock)
            self.receive_data(clientsock,once=True)

            # sends routing table to the newly connected peer
            rt = 'RT '
            for node in self.routing_table:
                rt += (f'{node}-{self.routing_table[node][0]} ')

            self.send_data(rt + ' ' * (1024 - len(rt)), clientsock)
            peer_alias = self.peer_aliases[clientsock]

            self.show_message(f'{peer_alias} has joined the server!\n')
            self.connected = True
            self.show_activepeers()
            self.broadcast(f'update_RT {self.alias} {peer_alias} {self.routing_table[peer_alias][0]}')
        
            # allows you to receive data from clientsock
            Thread(target=self.receive_data, args=(clientsock,)).start()
    
    def connect_to_peer(self, host, port: int, latency=1):
        # Generate another port to connect to other peers
        # if len(self.routing_table) == 1:
        try:
            connector_sock = socket(AF_INET, SOCK_STREAM)
            connector_sock.connect((host, port))
            self.connected = True
            self.send_data(f'WHOAMI {self.alias} {latency}', connector_sock)
            self.receive_data(connector_sock, once=True)
            peer_alias = self.peer_aliases[connector_sock]    
            self.routing_table[peer_alias] = (latency, peer_alias)
        except Exception as e:
            self.show_message(str(e) + "\n")

        # allows you to always receive data from the peer that you connected to
        Thread(target=self.receive_data, args=(connector_sock,)).start()
        self.send_data(f"direct_connect {self.alias} {peer_alias} {latency}", connector_sock)
        self.direct_connects.append(((self.alias,peer_alias),latency))

    ##### ---------- GUI FUNCTIONS ---------- #####
    def gui(self):
        '''GUI handler of Peer'''
        self.window = tk.Tk()
        self.window.title("P2P Chat App")
        self.window.resizable(0,0)

        #----------------------Styles
        self.window.columnconfigure(0, weight=6)
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=0)


        s = ttk.Style()
        s.configure('chats_frame.TFrame', background="#F7F7F7")
        s.configure('rightpane.TFrame', background="#F7F7F7")
        s.configure('input_msg_frame.TFrame', background="#F7F7F7")
        s.configure('header1.TLabel', background="#F7F7F7", font = ('Helvetica', 11, "bold"))
        s.configure('header2.TLabel', background="#F7F7F7", font = ('Helvetica', 10))

        #------------------------ Frames
        self.chats_frame = ttk.Frame(self.window, width=600, height=550, style='chats_frame.TFrame')
        self.chats_frame.grid(column=0, row=0, sticky="NESW")

        self.rightpane = ttk.Frame(self.window, width=200, height=600, style='rightpane.TFrame')
        self.rightpane.grid(column=1, row=0, rowspan=2, sticky="NESW")

        self.input_msg_frame = ttk.Frame(self.window, width=600, height=50, style='input_msg_frame.TFrame')
        self.input_msg_frame.grid(column=0, row=1, sticky="WE")

        #-------------------------widgets
        # input message frame
        self.input_widget = tk.Text(self.input_msg_frame, height=2, font = ("helvitica", 11))
        self.input_widget.grid(column=0, row=0, padx=5, pady=5, sticky="W")
        self.send_button_widget = tk.Button(self.input_msg_frame, text="Send", command=self.send_button)
        self.send_button_widget.grid(column=1, row=0, padx=5, pady=5)
        self.input_widget.bind("<Return>", lambda event: self.send_button_widget.invoke())

        # chat frame
        self.chats_widget = scrolledtext.ScrolledText(self.chats_frame)
        self.chats_widget.configure(height=30, width=83, font = ("helvitica", 11), state='disabled')
        self.chats_widget.grid(row=1, column=0, padx=5, pady=5)
        self.chats_label = ttk.Label(self.chats_frame, text="#Chatroom", style="header1.TLabel")
        self.chats_label.grid(row=0, column=0, padx=5, pady=5)

        # right pane frame
        self.joinserver_label = ttk.Label(self.rightpane, text='Connect to peer', style='header1.TLabel')
        self.joinserver_label.grid(row=0, column=0, padx=5, pady=5)

        self.peerip_label = ttk.Label(self.rightpane, text='Enter IP Address to connect:', style='header2.TLabel')
        self.peerip_label.grid(row=1, column=0, padx=5, pady=5)
        self.peerip_widget = tk.Entry(self.rightpane)
        self.peerip_widget.grid(row=2, column=0, padx=5, pady=5)

        self.peerport_label = ttk.Label(self.rightpane, text='Enter port to connect:', style='header2.TLabel')
        self.peerport_label.grid(row=3, column=0, padx=5, pady=5)
        self.peerport_widget = tk.Entry(self.rightpane)
        self.peerport_widget.grid(row=4, column=0, padx=5, pady=5)

        self.slatency_label = ttk.Label(self.rightpane, text='Simulated latency:', style='header2.TLabel')
        self.slatency_label.grid(row=5, column=0, padx=5, pady=5)
        self.slatency_widget = tk.Entry(self.rightpane)
        self.slatency_widget.grid(row=6, column=0, padx=5, pady=5)

        self.joinserver_button = tk.Button(self.rightpane, text="Join", command=self.join_button)
        self.joinserver_button.grid(row=7, column=0, padx=5, pady=5)

        self.userlist_label = ttk.Label(self.rightpane, text="Online Users", style="header1.TLabel")
        self.userlist_label.grid(row=8, column=0, padx=5, pady=5)
        self.userlist_widget = scrolledtext.ScrolledText(self.rightpane)
        self.userlist_widget.configure(height=15, width=20, font = ("helvitica", 11), state='disabled')
        self.userlist_widget.grid(row=9, column=0, padx=5, pady=5)

        self.init_info()
        self.window.mainloop()

    def send_button(self):
        """
        Captures event from the send button. Additionally, it contains handlers for specific commands sent.
        """
        msg_in = self.input_widget.get('1.0', 'end')

        if msg_in.isspace() or len(msg_in) == 0:
            pass
        elif msg_in.startswith("/pm"):
            try:
                if self.connected:
                    if len(msg_in.split(' ')) > 3: raise ValueError
                    _command, receiver, message= msg_in.split(' ')
                    if self.alias == receiver: 
                        self.show_message("Unless you're crazy, you can't whisper to yourself!\n")
                        return "break"
                    if receiver in self.routing_table:
                        self.broadcast(f"priv_msg {self.alias} {receiver} {message}")

                        self.show_message(f'[You whispered to {receiver}] {message}')
                    else:
                        self.show_message(f"{receiver} is not found!\n")
                else:
                    self.show_message("You can't privately message someone if you are not connected to a server.\n")
            except ValueError:
                self.show_message(f'Incorrect usage of the command. Use /pm <nick> <message>\n')

        elif msg_in.startswith("/ping"):
            try:
                if self.connected:
                    if len(msg_in.split(' ')) > 2: raise ValueError
                    _command, receiver = msg_in.split(' ')
                    d_peer = False
                    receiver = receiver[:-1]
                    for direct_peer in self.direct_connects:
                        if direct_peer[0] == (self.alias, receiver):
                            self.show_message(f'[You] Latency to {receiver} is {direct_peer[1]}\n')
                            d_peer = True
                    if d_peer == False:
                        self.show_message(f'[You] Latency to {receiver} is {self.routing_table[receiver][0]}\n')
                else:
                    self.show_message("You must be connected to a server before pinging to a peer.\n")
            except ValueError:
                self.show_message(f'Incorrect usage of the command. Use /ping <nick>\n')
            except KeyError:
                self.show_message(f"{receiver} is not found!\n")

        elif msg_in.startswith("/help") or msg_in.startswith("/h"):
            try:
                available_commands = ["connect", "c", "disconnect", "dc", "nickname", "nn", "pm", "ping"]
                if len(msg_in.split(' ')) > 2: raise ValueError
                if len(msg_in.split(' ')) == 1:
                    self.show_message(f'[You] You pressed /help. Here are the available commands: \n/connect or /c\n/disconnect or /dc\n/nickname or /nn\n/pm\n/ping\nTo view information about the command, type /help <command> or simply /h <command>\nExample Usage: /help connect\nDisplays: Information about the /connect command.\n')
                else:
                    msg_in = msg_in.replace("\n", "")
                    if msg_in.split(' ')[1] in available_commands:
                        if msg_in.split(' ')[1] == "connect" or msg_in.split(' ')[1] == "c":
                            self.show_message("/connect <name> <latency> or /c <name> <latency>\n This command connects directly to someone in the network. This command should only be used after connecting to a network.\n")
                        elif msg_in.split(' ')[1] == "disconnect" or msg_in.split(' ')[1] == "dc":
                            self.show_message("/disconnect or /dc\n This command disconnects you from the current network.\n")
                        elif msg_in.split(' ')[1] == "/nickname" or msg_in.split(' ')[1] == "nn":
                            self.show_message("/nickname <nickname> or /nn <nickname>\n This command changes your nickname in the network.\n")
                        elif msg_in.split(' ')[1] == "pm":
                            self.show_message("/pm <name> <message>\n This command allows you to send a private message to someone in the network.\n")
                        elif msg_in.split(' ')[1] == "ping":
                            self.show_message("/ping <name>\n This command allows you to check latency between a peer.\n")
                    else:
                        self.show_message(f"/{msg_in[1]} command is not found!\n")
            except ValueError:
                self.show_message(f'Incorrect usage of the command. /help or /h does not accept additional arguments!\n')
    
        elif msg_in.startswith("/p"):
            try:
                if len(msg_in.split(' ')) > 1: raise ValueError
                self.broadcast("printall hi")
                print(self.routing_table)
                print(self.direct_connects)
                print(self.peer_aliases)
            except ValueError:
                self.show_message(f'Incorrect usage of the command. /p does not accept additional arguments!\n')
            
        elif msg_in.startswith("/connect") or msg_in.startswith("/c"):
            try:
                if len(msg_in.split(' ')) > 3: raise ValueError
                if self.connected:
                    _command, receiver, latency = msg_in.split(' ')
                    latency = latency.replace("\n","")
                    
                    if not latency.isdigit(): raise TypeError
                    if receiver not in self.routing_table: raise KeyError
                    pair = (self.alias, receiver)
                    for pairs in self.direct_connects:
                        if pairs[0] == pair:
                            self.show_message(f"You are already connected to {receiver}!\n")
                            self.input_widget.delete('1.0', 'end')
                            return "break"
                    if self.alias == receiver:
                        self.show_message(f"You can't connect to yourself!\n")
                        self.input_widget.delete('1.0', 'end')
                        return "break"
                    self.broadcast(f"connect {self.alias} {receiver} {latency}")
                    self.direct_connects = [x for x in self.direct_connects if x[0] != pair]                           
                    self.direct_connects.append((pair, latency))
                    self.show_message(f"Connected to {receiver} with {latency}ms as latency.\n")
                else:
                    self.show_message("You must be connected to a server first to directly connect to a peer.\n")
            except TypeError:
                self.show_message(f"Latency must be a number!\n")
            except ValueError:
                self.show_message(f'Incorrect usage of the command. Use /connect <nick> <latency>\n')
            except KeyError:
                self.show_message(f"{receiver} is not found!\n")

        elif msg_in.startswith("/disconnect") or msg_in.startswith("/dc"):
            try:
                if len(msg_in.split(' ')) > 1: raise ValueError
                if self.connected:
                    self.routing_table = {}
                    self.routing_table[self.alias] = (0,'none')
                    self.direct_connects = []
                    self.userlist_widget.configure(state='normal')
                    self.userlist_widget.delete('1.0', 'end')
                    self.userlist_widget.configure(state='disabled')
                    self.broadcast(f"disconnect {self.alias}")
                    
                    self.peerport_widget.configure(state="normal")
                    self.slatency_widget.configure(state="normal")
                    self.peerip_widget.configure(state="normal")
                    self.joinserver_button.configure(state='normal')
                    self.show_message(f'You successfully disconnected from the server.\n')
                    self.connected = False
                else:
                    self.show_message("You are not connected to a server.\n")
            except ValueError:
                self.show_message(f'Incorrect usage of the command. /disconnect or /dc does not accept additional arguments!\n')

        elif msg_in.startswith("/nickname") or msg_in.startswith("/nn"):
            try:
                if len(msg_in.split(' ')) > 2: raise ValueError
                self.broadcast(f"gMSG {self.alias} {self.alias} set their nickname to {msg_in.split(' ')[1]}")
                self.broadcast(f"nickname {self.alias} {msg_in.split(' ')[1]}")
                self.change_nickname(msg_in.split(' ')[1][:-1])
                self.show_message(f'[You] You set your nickname to {self.alias}\n')
            except ValueError:
                self.show_message(f'Incorrect usage of the command. Use /nickname <nickname> or /nn <nickname>\n')

        elif msg_in.startswith("/"):
            self.show_message("You have entered an incorrect command. For a list of commands, please refer to /help\n")

        else:
            # send message to peers
            self.broadcast(f"gMSG {self.alias} {msg_in}")
            self.show_message(f'[You] {msg_in}')

        self.input_widget.delete('1.0', 'end')
        return "break"


    def join_button(self):
        ''' Execute once the join button is pressed'''
        ip = self.peerip_widget.get()
        port = self.peerport_widget.get()
        latency = self.slatency_widget.get()

        if port.isdigit() and latency.isdigit():
            self.connect_to_peer(ip, int(port), int(latency))
            self.peerip_widget.configure(state="disabled")
            self.peerport_widget.configure(state="disabled")
            self.slatency_widget.configure(state="disabled")
            self.joinserver_button.configure(state='disabled')
        else:
            messagebox.showerror(message="Input is invalid. Please try again.")
    
    def show_message(self, message:str):
        '''GUI Helper Function: Shows `message` on the chatbox'''
        self.chats_widget.configure(state='normal')
        self.chats_widget.insert('end', message)
        self.chats_widget.yview('end')
        self.chats_widget.configure(state='disabled')

    def show_activepeers(self):
        '''GUI Helper Function: Shows all connected peers in the server'''
        self.userlist_widget.configure(state='normal')
        self.userlist_widget.delete("1.0", "end")
        for i in self.routing_table:
            self.userlist_widget.insert('end', i+"\n")
            # if self.alias != i:
            #     self.userlist_widget.insert('end', i+"\n")
        self.userlist_widget.yview('end')
        self.userlist_widget.configure(state='disabled')


class GUIStartUp:
    def __init__(self) -> None:
        ### Set-up Window GUI ###
        self.setup_win = tk.Tk()
        self.setup_win.eval('tk::PlaceWindow . center')
        self.setup_win.title("P2P Chat App (User set-up)")
        self.setup_win.minsize(340, 100)
        self.setup_win.columnconfigure(0, weight=1)
        self.setup_win.columnconfigure(1, weight=4)
        ## labels ##
        self.port_l = tk.Label(self.setup_win, text="Port:")
        self.name_l = tk.Label(self.setup_win, text='Name:')
        self.instructions = tk.Label(self.setup_win, text="Welcome to the P2P Chat App!\nKindly input the port you would like to open so that other clients will be able to connect to you. Don't forget your personal nickname!", wraplength=300)
        ## input ##
        self.in_port = tk.Entry(self.setup_win)
        self.in_name = tk.Entry(self.setup_win)
        self.conn_button = tk.Button(self.setup_win, text="Connect", command=self.submit)
        self.setup_win.bind("<Return>", lambda event: self.conn_button.invoke())
        ## Layout ##
        self.instructions.grid(row = 0, columnspan=2, padx=5, pady=5)
        self.port_l.grid(row=1, column=0, padx=5, pady=5)
        self.in_port.grid(row=1, column=1, padx=5, pady=5)
        self.name_l.grid(row=2, column=0, padx=5, pady=5)
        self.in_name.grid(row=2, column=1, padx=5, pady=5)
        self.conn_button.grid(row=3, column=1 , padx=5, pady=5)
        
        ## Error Booleans ##
        self.wrong_port = False
        self.wrong_name = False
        self.setup_win.resizable(False, False)
        self.setup_win.mainloop()
    
    def submit(self):
        try:
            if not self.in_port.get().isdigit() and self.in_name.get() == '' or self.in_name.get().isspace():
                self.wrong_port, self.wrong_name = True, True
            if self.in_port.get().isdigit():
                if int(self.in_port.get()) >= 65535 or int(self.in_port.get()) < 0:
                    self.wrong_port = True
                    raise ValueError
            if not self.in_port.get().isdigit(): 
                self.wrong_port = True
                raise ValueError
            if self.in_name.get() == '' or self.in_name.get().isspace():
                self.wrong_name = True
                raise ValueError
            if int(self.in_port.get()) < 49152:
                confirm = askyesno("Security Warning", "We generally recommend to open ports between 49152 and 65535. Anything below can compromise security. Are you sure you want to continue?")
                if confirm:
                    pass
                else: return
            self.wrong_port, self.wrong_name = False, False
            self.port = int(self.in_port.get())
            self.name = self.in_name.get()
            self.name = self.name.replace(" ", "")
            self.setup_win.destroy()
            host = gethostname()
            ip = gethostbyname(host)
            self.peer = (Peer(ip, self.port, self.name))
            Thread(target=self.peer.allow_connection).start()
        except ValueError:
            if self.wrong_port and self.wrong_name:
                if len(self.in_port.get()) == 0 or self.in_port.get().isspace():
                    messagebox.showerror("Port & Name Error", f"You entered a blank port and a blank name. A port should be a number and a name must not be blank!")
                elif self.in_port.get().isdigit():
                    if int(self.in_port.get()) >= 65535 or int(self.in_port.get()) < 0:
                        messagebox.showerror("Port Out of Range & Name Error", f"You entered Port {self.in_port.get()} and a blank name. A port should be between 0-65535 and a name must not be blank!")
                else:
                    messagebox.showerror("Port & Name Error", f"You entered Port {self.in_port.get()} and a blank name. A port should be a number and a name must not be blank!")
                self.wrong_port, self.wrong_name = False, False
            elif self.wrong_port:
                if len(self.in_port.get()) == 0 or self.in_port.get().isspace():
                    messagebox.showerror("Port Error", f"You entered a blank port. A port should be a number!")
                elif self.in_port.get().isdigit():
                    if int(self.in_port.get()) >= 65535:
                        messagebox.showerror("Port Out of Range Error", f"You entered Port {self.in_port.get()}. A port should be between 0-65535!")
                else:
                    messagebox.showerror("Port Error", f"You entered Port {self.in_port.get()}. A port should be a number!")
                self.wrong_port, self.wrong_name = False, False
            elif self.wrong_name:
                messagebox.showerror("Name Error", "You entered a blank name. A name should not be blank!")
                self.wrong_port, self.wrong_name = False, False

if __name__ == '__main__':
    start = GUIStartUp()