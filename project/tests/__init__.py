import collections
import dataclasses
import socket
import threading
import typing
import unittest

from jl95.batteries import CompletableFuture as _CompletableFuture, Future as _Future
import jl95.net.io as _net_io

from ..package import util

TEST_PORT=53536
TEST_ADDRESS=("127.0.0.1",TEST_PORT,)

@dataclasses.dataclass
class TestExchange:
    request:str
    response:str

class Tests(unittest.TestCase):

    def _test(self, rpcs:typing.Iterable[TestExchange]):

        server = socket.socket()
        server.bind(TEST_ADDRESS)
        server.listen(1)
        rsock_future = _CompletableFuture[socket.socket]()
        def get_receiver():
            rsock, addr = server.accept()
            rsock_future.complete(rsock)
            server.close()
        rt = threading.Thread(target=get_receiver)
        rt.start()
        ssock = socket.socket()
        ssock.connect(TEST_ADDRESS)
        rt.join()
        rsock = rsock_future.get(timeout=3)
        requester = util.requester_from_socket(ssock).adapted(str.encode, bytes.decode)
        responder = util.responder_from_socket(rsock).adapted(bytes.decode, str.encode)
        remaining = collections.deque(rpcs)
        def rh(request:str):
            print(f"Received request: {request}")
            response = request + ", " + remaining.popleft().response
            return (response,bool(remaining),)
        threading.Thread(target=lambda: responder.respond_while(rh)).start()
        for rpc in rpcs:
            print(rpc)
            self.assertEqual(requester(rpc.request).get(timeout=3), rpc.request + ", " + rpc.response)
        ssock.close()
        rsock.close()

    def test(self):

        self._test([
            TestExchange(request="Hello", response="World"),
            TestExchange(request="Foo",   response="Bar"),
            TestExchange(request="Ping",  response="Pong"),
        ])
