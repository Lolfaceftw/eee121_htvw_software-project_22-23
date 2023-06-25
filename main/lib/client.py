import socket
import threading
import tkinter as tk

class Client():
    def get_free_port():
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_socket.bind(("", 0))
        free_port = temp_socket.getsockname()[1]
        temp_socket.close()

        ### This get_free_port() is used to get the port that is free for use.
        ### Take note that if you want to print your port, dapat port-1, look sa may baba later.
        return free_port

    def get_local_ip():
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(("8.8.8.8", 80))
        local_ip = temp_socket.getsockname()[0]
        temp_socket.close()

        ### DGRAM was used instead since connectionless siya. This is so that the sent dummy datagram is used to retrieve
        ### the local IP assigned by the network to the device.

        return local_ip