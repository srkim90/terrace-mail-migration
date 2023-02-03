
import socket
import sys
import threading

def main():
    try:
        host_ipaddr = sys.argv[1]
    except KeyError:
        host_ipaddr = "127.0.0.1"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host_ipaddr, 5222))
        s.sendall(b"Hello, world")
        data = s.recv(1024)
    return

if __name__ == "__main__":
    main()
