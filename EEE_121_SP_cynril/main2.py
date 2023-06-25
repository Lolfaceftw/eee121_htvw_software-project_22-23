from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

class Peer:
    def __init__(self, u_host, u_port: int, alias: str=''):
        self.host = u_host
        self.port = u_port
        self.alias = alias
        self.u_socket = socket(AF_INET, SOCK_STREAM)
        self.routing_table = {} # dict{alias : tuple(latency, hop)}
        self.peer_aliases = {} # dict{socket : alias}
        self.table = []

    def receive_data(self, client_socket: socket, once=False):
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            command, info = data.split(' ', 1)
            if command == 'MSG':
                for peer in self.peer_aliases:
                    if peer == client_socket:
                        print(f'[{self.peer_aliases[peer]}]',info)
                        break
            
            elif command == 'WHOAMI':
                alias, latency = info.split(' ',1)
                self.peer_aliases[client_socket] = alias
                if latency == 'to_set':
                    break
                self.routing_table[alias] = (int(latency),alias) 
                if once:
                    break
            
            elif command == "RT":
                print(info)
                table = info.split()
                print(table)
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

            elif command == "update_RT":
                sender, new_peer, latency = info.split()
                print(f'{new_peer} has joined the server!')
                if new_peer not in self.routing_table:
                    print(self.routing_table[sender][0] ,'+', int(latency))
                    distance = self.routing_table[sender][0] + int(latency)
                    self.routing_table[new_peer] = (distance, sender)
                
                for peersock in self.peer_aliases:
                    if self.peer_aliases[peersock] != sender:
                        self.send_data(f'update_RT {self.alias} {new_peer} {self.routing_table[sender][0] + int(latency)}',peersock)

                

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
        self.u_socket.bind((self.host, self.port))
        self.u_socket.listen(5)
        self.routing_table[self.alias] = (0,'none')
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
            self.broadcast(f'update_RT {self.alias} {peer_alias} {self.routing_table[peer_alias][0]}')
        
            # allows you to receive data from clientsock
            Thread(target=self.receive_data, args=(clientsock,)).start()
    
    def connect_to_peer(self, host, port: int, latency=1):
        # Generate another port to connect to other peers
        connector_sock = socket(AF_INET, SOCK_STREAM)
        connector_sock.connect((host, port))
        self.send_data(f'WHOAMI {self.alias} {latency}', connector_sock)
        self.receive_data(connector_sock, once=True)
        peer_alias = self.peer_aliases[connector_sock]    
        self.routing_table[peer_alias] = (latency, peer_alias)

        # allows you to always receive data from the peer that you connected to
        Thread(target=self.receive_data, args=(connector_sock,)).start()


if __name__ == '__main__':
    print('-----User setup-----')
    porty = int(input('Port: '))
    name = input('Name: ')
    peer = Peer('localhost', porty, alias=name)
    Thread(target=peer.allow_connection).start()

    while True:
        print('Choose mode:\n[1] Connect to peer\n[2] Send message\n[3]Check routing table')
        choice = input('>>')
        if choice == '1':
            connect_to = int(input("Input peer port to connect: "))
            simul_latency = int(input("Simulated latency: "))
            peer.connect_to_peer('localhost', connect_to, simul_latency)
        elif choice == '2':
            message = input('send message: ')
            peer.broadcast(f'MSG {message}')
        elif choice == '3':
            print(peer.routing_table)

        else:
            print("invalid option. try again")