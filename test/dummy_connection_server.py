
import socket
import sys
import threading


def handle_client(connection, address):
    buf = connection.recv(1024)
    connection.send(buf)
    connection.close()

def start_threads(connection, address):
    h_thread = threading.Thread(target=handle_client, args=(connection, address))
    h_thread.daemon = True
    h_thread.start()

g_sockets = []
def keep_socket(connection, address):
    global g_sockets
    g_sockets.append((connection, address))

def main():
    try:
        host_ipaddr = sys.argv[1]
    except IndexError:
        host_ipaddr = "127.0.0.1"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host_ipaddr, 5222))
    sock.listen(500)

    while True:
        connection, address = sock.accept()
        keep_socket(connection, address)



if __name__ == "__main__":
    main()
