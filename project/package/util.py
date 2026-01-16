from . import (BytesIOSRRequester as _Requester,
               BytesIOSRResponder as _Responder)
import socket as _socket

import jl95.net.io.util as _net_io

def requester_from_socket(sock: _socket.socket):

    return _Requester(_net_io.sender_from_socket(sock),
                      _net_io.receiver_from_socket(sock))

def responder_from_socket(sock: _socket.socket):

    return _Responder(_net_io.receiver_from_socket(sock),
                      _net_io.sender_from_socket(sock))
