import socket

from project.package import *
from project.package import util

server = socket.socket()
server.bind(("127.0.0.1", 4243,))
print("Bound")
server.listen(1)
sock, addr = server.accept()
print("Accepted")
server.close()
responder = util.responder_from_socket(sock).adapted(bytes.decode, str.encode)
def respond(msg:str):
    print(f"<<< {msg}")
    rmsg = f"{repr(msg)} has {len(msg)} characters"
    print(f">>> {rmsg}")
    return rmsg
responder.respond_forever(respond)
sock.close()
print("Done.")
