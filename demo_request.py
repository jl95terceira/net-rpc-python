import socket

from project.package import *
from project.package import util

sock = socket.socket()
sock.connect(("127.0.0.1", 4243,))
print("Connect")
requester = util.requester_from_socket(sock).adapted(str.encode, bytes.decode)
n_empty = 0
while True:
    request = input(">>> ")
    if not request:
        n_empty += 1
        if n_empty >= 2:
            break
        continue
    n_empty = 0
    print("<<< "+requester(request).get(3.0))
requester.close()
print("Done.")
