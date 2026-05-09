import argparse
import socket

from project.package import *
from project.package import util

def demo(addr,
         on_bounded=lambda: print("Bound"),
         on_accepted=lambda: print("Accepted"),
         on_request=lambda re: print(f"<<< {re}"),
         get_response=lambda re: input(">>> ")):

    server = socket.socket()
    server.bind(addr)
    on_bounded()
    server.listen(1)
    sock, addr = server.accept()
    on_accepted()
    server.close()
    responder = util.responder_from_socket(sock).adapted(bytes.decode, str.encode)
    def respond(request:str):
        on_request(request)
        return get_response(request)
    try:
        responder.respond_forever(respond)
    except KeyboardInterrupt:
        pass
    responder.close()
    print("Done.")

def main():
    
    ap = argparse.ArgumentParser()
    class Defaults:
        IP_ADDR = "127.0.0.1:4243"
    ap.add_argument("--ip-addr","-a",
                    help=f"IP address of peer requester",
                    default=Defaults.IP_ADDR)
    ap.add_argument("--count",
                    help=f"Instead of manually responding, automatically count the characters in the request and return it descriptively",
                    action="store_true")
    get = ap.parse_args().__getattribute__
    ip_addr_repr:str  = get("ip_addr")
    count       :bool = get("count")
    ip_addr = (lambda i: (
        ip_addr_repr[:i],
        int(ip_addr_repr[1+i:]),
    ))(ip_addr_repr.find(":"))
    if not count:
        demo(ip_addr)
    else:
        demo(ip_addr, get_response=lambda re: f"{repr(re)} has {len(re)} characters")

if __name__ == "__main__": main()
