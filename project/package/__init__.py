import abc as _abc
import threading as _threading
import typing as _typing
from uuid import uuid4 as _uuid4

from jl95 import batteries as _b
from jl95.net import io as _net_io

class Closeable(_net_io.Closeable, _typing.Protocol): pass

class Requester[A,R](Closeable, _typing.Protocol):

    @_abc.abstractmethod
    def __call__(self, data:A) -> _b.Future[R]: ...

class IOSRRequester[A,R](Requester[A,R]):

    @_abc.abstractmethod
    def serialize(self, data:A) -> bytes: ...

    @_abc.abstractmethod
    def deserialize(self, data:bytes) -> R: ...

    def __init__(self,
                 sender  :_net_io.Sender  [bytes], 
                 receiver:_net_io.Receiver[bytes]):

        self._sender = sender
        self._receiver = receiver
        self._is_receiving = False
        self._response_futures_dict:dict[str, _b.CompletableFuture[bytes]] = dict()
        self._response_futures_dict_lock = _threading.Lock()

    def _handler(self, response:bytes): 
        
            request_id_as_bytes = response[36:72]
            payload             = response[72:]
            request_id          = request_id_as_bytes.decode('utf-8')
            if request_id in self._response_futures_dict:
                self._response_futures_dict[request_id].complete(payload)
                del self._response_futures_dict[request_id]
                self._is_receiving = False
            return bool(self._response_futures_dict)
    
    def _start_recv(self):

        _threading.Thread(target=lambda: self._receiver.recv_while(self._handler)).start()
        self._is_receiving = True

    @_typing.override
    def __call__(self, data:A) -> _b.Future[R]:
        
        payload = self.serialize(data)
        response_future = _b.CompletableFuture[bytes]()
        request_id = str(_uuid4())
        self._response_futures_dict[request_id] = response_future
        request_id_as_bytes = request_id.encode('utf-8')
        request = request_id_as_bytes + payload
        if not self._is_receiving:
            self._start_recv()
        self._sender.send(request)
        return response_future.map(self.deserialize)
    
    @_typing.override
    def close(self):

        self._receiver.close()
        self._sender  .close()

    def adapted[A2,R2](self, 
                       fser  :_typing.Callable[[A2], A], 
                       fdeser:_typing.Callable[[R], R2]) -> 'IOSRRequester[A2,R2]':
        
        parent = self

        class AdaptedRequester(IOSRRequester[A2,R2]):

            @_typing.override
            def serialize(self, data:A2) -> bytes:
                return parent.serialize(fser(data))

            @_typing.override
            def deserialize(self, data:bytes) -> R2:
                return fdeser(parent.deserialize(data))
        
        return AdaptedRequester(self._sender, self._receiver)
    
    def adapted_request[A2](self,
                            fser  :_typing.Callable[[A2], A]) -> 'IOSRRequester[A2, R]':
    
          return self.adapted(fser, lambda x: x)
    
    def adapted_response[R2](self,
                             fdeser:_typing.Callable[[R], R2]) -> 'IOSRRequester[A, R2]':

          return self.adapted(lambda x: x, fdeser)

class BytesIOSRRequester(IOSRRequester[bytes, bytes]):

    @_typing.override
    def serialize(self, data:bytes) -> bytes: return data # as-is

    @_typing.override
    def deserialize(self, data:bytes) -> bytes: return data # as-is

class Responder[A,R](Closeable, _typing.Protocol):

    @_abc.abstractmethod
    def respond_while(self, handler:_typing.Callable[[A], tuple[R,bool]]): ...

    def respond_forever(self, handler:_typing.Callable[[A], R]):

        self.respond_while(lambda data: (handler(data), True,))

    def respond_once(self, handler:_typing.Callable[[A], R]):

        self.respond_while(lambda data: (handler(data), False,))

class IOSRResponder[A,R](Responder[A,R]):

    @_abc.abstractmethod
    def deserialize(self, data:bytes) -> A: ...

    @_abc.abstractmethod
    def serialize(self, data:R) -> bytes: ...

    def __init__(self,
                 receiver:_net_io.Receiver[bytes],
                 sender  :_net_io.Sender  [bytes]):

        self._sender       = sender
        self._receiver     = receiver

    def _handle(self, request:bytes, handler:_typing.Callable[[A], tuple[R, bool]]) -> bool: 

        requestIdAsBytes = request[0:36]
        requestPayload   = request[36:]
        object = handler(self.deserialize(requestPayload))
        responsePayload = self.serialize(object[0])
        try:
            responseIdAsBytes = str(_uuid4()).encode('utf-8')
            response = responseIdAsBytes + requestIdAsBytes + responsePayload
            self._sender.send(response)
        except Exception:
            return True # continue receiving
        return object[1]

    @_typing.override
    def respond_while(self, handler: _typing.Callable[[A], tuple[R, bool]]):
        
        self._receiver.recv_while(lambda request: self._handle(request, handler))

    @_typing.override
    def close(self):

        self._receiver.close()
        self._sender  .close()

    def adapted[A2,R2](self, 
                       fdeser:_typing.Callable[[A], A2], 
                       fser  :_typing.Callable[[R2], R]) -> 'IOSRResponder[A2,R2]':

        parent = self

        class AdaptedResponder(IOSRResponder[A2,R2]):

            @_typing.override
            def deserialize(self, data:bytes) -> A2:
                return fdeser(parent.deserialize(data))

            @_typing.override
            def serialize(self, data:R2) -> bytes:
                return parent.serialize(fser(data))
        
        return AdaptedResponder(self._receiver, self._sender)

    def adapted_request[A2](self, 
                           fdeser:_typing.Callable[[A], A2]) -> 'IOSRResponder[A2, R]':

        return self.adapted(fdeser, lambda x: x)

    def adapted_response[R2](self, 
                            fser  :_typing.Callable[[R2], R]) -> 'IOSRResponder[A, R2]':

        return self.adapted(lambda x: x, fser)

class BytesIOSRResponder(IOSRResponder[bytes, bytes]):

    @_typing.override
    def deserialize(self, data:bytes) -> bytes: return data # as-is
    
    @_typing.override
    def serialize(self, data:bytes) -> bytes: return data # as-is
