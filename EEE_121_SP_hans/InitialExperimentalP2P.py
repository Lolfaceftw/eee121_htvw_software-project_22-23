import socket
import tkinter as tk
import threading

def get_free_port():
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_socket.bind(("", 0))
    free_port = temp_socket.getsockname()[1]
    temp_socket.close()
    return free_port

def get_local_ip():
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    temp_socket.connect(("8.8.8.8", 80))
    local_ip = temp_socket.getsockname()[0]
    temp_socket.close()
    return local_ip

def send_message():
    receiver_ip = receiver_ip_entry.get()
    receiver_port = int(receiver_port_entry.get())
    message = message_entry.get()

    send_thread = threading.Thread(target=send_message_thread, args=(receiver_ip, receiver_port, message))
    send_thread.start()

def send_message_thread(receiver_ip, receiver_port, message):
    try:
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect((receiver_ip, receiver_port))
        send_socket.sendall(message.encode())
        send_socket.close()

        sent_messages.append(f"Sent message to {receiver_ip}:{receiver_port}: {message}")
        message_box.insert(tk.END, f"Sent message to {receiver_ip}:{receiver_port}: {message}\n")

        message_entry.delete(0, tk.END)
    except Exception as e:
        error_message = f"Failed to send message to {receiver_ip}:{receiver_port}: {str(e)}"
        sent_messages.append(error_message)
        message_box.insert(tk.END, error_message + "\n")

def receive_messages():
    receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    receive_socket.bind((local_ip, receive_port))
    receive_socket.listen(5)

    while True:
        conn, address = receive_socket.accept()

        receive_thread = threading.Thread(target=receive_message_thread, args=(conn, address))
        receive_thread.start()

def receive_message_thread(conn, address):
    try:
        data = conn.recv(1024).decode()
        message = data

        received_messages.append(f"Received message from {address[0]}:{address[1]}: {message}")
        message_box.insert(tk.END, f"Received message from {address[0]}:{address[1]}: {message}\n")

        conn.close()
    except Exception as e:
        error_message = f"Failed to receive message from {address[0]}:{address[1]}: {str(e)}"
        received_messages.append(error_message)
        message_box.insert(tk.END, error_message + "\n")

window = tk.Tk()

local_ip = get_local_ip()
receive_port = get_free_port()

print(get_local_ip())
print(str(int(get_free_port())-1))


receiver_ip_label = tk.Label(window, text="Receiver IP:")
receiver_ip_label.pack()
receiver_ip_entry = tk.Entry(window)
receiver_ip_entry.pack()

receiver_port_label = tk.Label(window, text="Receiver Port:")
receiver_port_label.pack()
receiver_port_entry = tk.Entry(window)
receiver_port_entry.pack()
receiver_port_entry.insert(0, receive_port)

message_label = tk.Label(window, text="Message:")
message_label.pack()
message_entry = tk.Entry(window)
message_entry.pack()

send_button = tk.Button(window, text="Send", command=send_message)
send_button.pack()

received_messages = []
sent_messages = []

message_box = tk.Text(window)
message_box.pack()

receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

window.mainloop()
