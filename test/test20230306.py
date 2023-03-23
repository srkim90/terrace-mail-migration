import sys
import telnetlib
import socket

def main():
    scan_opt = sys.argv[1]
    file_path = sys.argv[2]

    HOST = "10.0.1.17"
    PORT = 4010

    timeout_seconds=3

    if len(sys.argv) != 3:
            print("telnet.py [option] [file(folder) path]")
            sys.exit()

    print("option : " + scan_opt)
    print("path : " + file_path)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_seconds)
    result = sock.connect_ex((HOST,int(PORT)))

    if result == 0:
        print("Host: {}, Port: {} - True".format(HOST, PORT))
    else:
        print("Host: {}, Port: {} - False".format(HOST, PORT))

    sock.send("test message\r\n".encode())

    print(sock.recv(100).decode())
    while True:
        msg = input()
        sock.sendall(msg.encode(encoding='utf-8'))
        data = sock.recv(100)
        msg = data.decode()
        print('echo msg:', msg)

        if msg == '/end':
            break


if __name__ == "__main__":
    main()
