import argparse
import socket
import typing

from project.package import *
from project.package import util

def demo(addr,
         on_connected=lambda   : print("Connected"),
         get_request =lambda   : input(">>> "),
         on_response =lambda re: print(f"<<< {re}"),
         on_closed   =lambda   : print("Done.")):

    sock = socket.socket()
    sock.connect(addr)
    on_connected()
    requester = util.requester_from_socket(sock).adapted(str.encode, bytes.decode)
    n_empty = 0
    while True:
        request = get_request()
        if not request:
            n_empty += 1
            if n_empty >= 2:
                break
            continue
        n_empty = 0
        on_response(requester(request).get(10))
    requester.close()
    on_closed()

def main():

    ap = argparse.ArgumentParser()
    class Defaults:
        IP_ADDR = "127.0.0.1:4243"
    ap.add_argument("--ip-addr","-a",
                    help=f"IP address to connect",
                    default=Defaults.IP_ADDR)
    get = ap.parse_args().__getattribute__
    ip_addr_repr:str = get("ip_addr")
    ip_addr = (lambda i: (
        ip_addr_repr[:i],
        int(ip_addr_repr[1+i:]),
    ))(ip_addr_repr.find(":"))
    demo(ip_addr)

if __name__ == "__main__": main()
