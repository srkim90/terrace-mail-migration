
import socket
import sys
import time

def main():
    try:
        host_ipaddr = sys.argv[1]
        count = int(sys.argv[2])
    except IndexError:
        host_ipaddr = "127.0.0.1"
        count = 1
    socket_list = []
    for idx in range(count):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host_ipaddr, 5222))
            s.sendall(b"1")
        except OSError:
            print("stop connection %s: %d" % (host_ipaddr, idx,))
            break
        socket_list.append(s)
        print("connection to %s: %d" % (host_ipaddr, idx,))
    time.sleep(60*60*24)
    return

if __name__ == "__main__":
    main()
