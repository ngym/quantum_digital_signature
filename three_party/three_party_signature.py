from SimulaQron.general.hostConfig import *
from SimulaQron.cqc.backend.cqcHeader import *
from SimulaQron.cqc.pythonLib.cqc import *
import random
import asyncio

'''
This code's algorithm is originally from Secure Quantum Signatures Using Insecure Quantum Channels[1]

[1] https://arxiv.org/abs/1507.02975

topology.ini:
{"Alice": ["Bob","Charlie"], "Bob": ["Alice"], "Charlie": ["Alice"]}

Copyright 2018 Hirotaka Nakajima <github.com/nunnun>
This software is released under the MIT License.
'''

KEY_LENGTH = 48
S_A = 1 / 4
S_V = 1 / 3

class NodeType(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(NodeType, cls).__call__(*args, **kwargs)

        return cls._instance

class Alice(object):

    __metaclass__ = NodeType

    def __init__(self, _conn):
        self._conn = _conn
        self._keyring_to_bob_0 = []
        self._keyring_to_bob_1 = []
        self._keyring_to_charlie_0 = []
        self._keyring_to_charlie_1 = []
        self.__distribute()

    def __distribute(self):
        for i in range(KEY_LENGTH):
            k = self._conn.createEPR("Bob")
            self._keyring_to_bob_0.append(k.measure())
        for i in range(KEY_LENGTH):
            k = self._conn.createEPR("Bob")
            self._keyring_to_bob_1.append(k.measure())
        for i in range(KEY_LENGTH):
            k = self._conn.createEPR("Charlie")
            self._keyring_to_charlie_0.append(k.measure())
        for i in range(KEY_LENGTH):
            k = self._conn.createEPR("Charlie")
            self._keyring_to_charlie_1.append(k.measure())

    def send(self, msg):
        _payload = [msg]
        if 0 == msg:
            _payload += self._keyring_to_bob_0
            _payload += self._keyring_to_charlie_0
        else:
            _payload += self._keyring_to_bob_1
            _payload += self._keyring_to_charlie_1
        self._conn.sendClassical("Bob", _payload)

class Receiver(object):
    __metaclass__ = NodeType
    randomness = random.random()

    def __init__(self, _conn):
        self._conn = _conn
        self._keyring_to_alice_0 = []
        self._keyring_to_alice_1 = []
        self._private_key_0 = []
        self._private_key_1 = []
        self._received_key_0 = []
        self._received_key_1 = []
        self._secure_index = 0
        self._msg = None
        self._sig = []
        self.__distribute()

    def __distribute(self):
        for i in range(KEY_LENGTH):
            k = self._conn.recvEPR()
            self._keyring_to_alice_0.append(k.measure())
        for i in range(KEY_LENGTH):
            k = self._conn.recvEPR()
            self._keyring_to_alice_1.append(k.measure())

    def send_symmetric_key(self, dest):
        # print(self.__class__.__name__ + ": send_symmetric_key")
        _index = int(KEY_LENGTH / 2)
        if 0.5 > self.randomness:
            _keyslice_0 = self._keyring_to_alice_0[_index:]
            self._private_key_0 = self._keyring_to_alice_0[:_index]
            _keyslice_1 = self._keyring_to_alice_1[_index:]
            self._private_key_1 = self._keyring_to_alice_1[:_index]
        else:
            _keyslice_0 = self._keyring_to_alice_0[:_index]
            self._private_key_0 = self._keyring_to_alice_0[_index:]
            _keyslice_1 = self._keyring_to_alice_1[:_index]
            self._private_key_1 = self._keyring_to_alice_1[_index:]
        self._conn.sendClassical(dest._conn.name, _keyslice_0 + _keyslice_1)

    def recv_symmetric_key(self):
        # print(self.__class__.__name__ + ": recv_symmetric_key")
        _data = list(self._conn.recvClassical())
        _index = int(KEY_LENGTH / 2)
        self._received_key_0 = _data[:_index]
        self._received_key_1 = _data[_index:]
        # print(self.__class__.__name__ + ": received")
        # print(_data)

    def validate(self):
        self._recv_msg()
        self._validate()

    def _recv_msg(self):
        self._recv_raw_data = list(self._conn.recvClassical())
        self._msg = self._recv_raw_data[0]
        self._sig.append(self._recv_raw_data[1:KEY_LENGTH + 1])
        self._sig.append(self._recv_raw_data[KEY_LENGTH + 1:])

    def _validate(self):
        _index = int(KEY_LENGTH / 2)
        if self._msg == 0:
            _priv_key = self._private_key_0
            _recv_key = self._received_key_0
        else:
            _priv_key = self._private_key_1
            _recv_key = self._received_key_1
        if "Bob" == self.__class__.__name__:
            sig_fail_self = 0
            sig_fail_peer = 0
            if 0.5 > self.randomness:
                for i in range(_index):
                    if self._sig[0][:_index][i] != _priv_key[i]:
                        sig_fail_self += 1
                    if self._sig[1][_index:][i] != _recv_key[i]:
                        sig_fail_peer += 1
            else:
                for i in range(_index):
                    if self._sig[0][_index:][i] != _priv_key[i]:
                        sig_fail_self += 1
                    if self._sig[1][:_index][i] != _recv_key[i]:
                        sig_fail_peer += 1
            self_error_rate = sig_fail_self / KEY_LENGTH
            peer_error_rate = sig_fail_peer / KEY_LENGTH
            if self_error_rate > S_A:
                raise Exception(
                    "Signature validation failed at {}, Self error rate: {}".format(self.__class__.__name__, self_error_rate))
            if peer_error_rate > S_A:
                raise Exception(
                    "Signature validation failed at {}, Self error rate: {}".format(self.__class__.__name__, peer_error_rate))
            to_print = "Validation Succeeded Node: {}, Self Error rate: {}, Peer Error rate: {}".format(
                self.__class__.__name__, self_error_rate, peer_error_rate)
            print("|"+"-"*(len(to_print)+2)+"|")
            print("| "+to_print+" |")
            print("|"+"-"*(len(to_print)+2)+"|")
            return
        elif "Charlie" == self.__class__.__name__:
            sig_fail_self = 0
            sig_fail_peer = 0
            if 0.5 > self.randomness:
                for i in range(_index):
                    if self._sig[1][:_index][i] != _priv_key[i]:
                        sig_fail_self += 1
                    if self._sig[0][_index:][i] != _recv_key[i]:
                        sig_fail_peer += 1
            else:
                for i in range(_index):
                    if self._sig[1][_index:][i] != _priv_key[i]:
                        sig_fail_self += 1
                    if self._sig[0][:_index][i] != _recv_key[i]:
                        sig_fail_peer += 1
            self_error_rate = sig_fail_self / KEY_LENGTH
            peer_error_rate = sig_fail_peer / KEY_LENGTH
            if self_error_rate > S_V:
                raise Exception(
                    "Signature validation failed at {}, Self error rate: {}".format(self.__class__.__name__, self_error_rate))
            if peer_error_rate > S_V:
                raise Exception(
                    "Signature validation failed at {}, Self error rate: {}".format(self.__class__.__name__, peer_error_rate))
            to_print = "Validation Succeeded Node: {}, Self Error rate: {}, Peer Error rate: {}".format(
                self.__class__.__name__, self_error_rate, peer_error_rate)
            print("|"+"-"*(len(to_print)+2)+"|")
            print("| "+to_print+" |")
            print("|"+"-"*(len(to_print)+2)+"|")
            return
        else:
            raise Exception("Instance must be an instance of Bob or Charlie")


class Bob(Receiver):

    def forward_to_charlie(self):
        self._conn.sendClassical("Charlie", self._recv_raw_data)

class Charlie(Receiver):
    pass

def main():
    with CQCConnection("Alice") as conn_alice, CQCConnection("Bob") as conn_bob, CQCConnection("Charlie") as conn_charlie:
        # Distribution stage
        a = Alice(conn_alice)
        b = Bob(conn_bob)
        c = Charlie(conn_charlie)

        loop = asyncio.get_event_loop()

        # Symmetrize keys between Bob and Charlie
        loop.run_until_complete(asyncio.gather(
            loop.run_in_executor(None, b.send_symmetric_key, c),
            loop.run_in_executor(None, c.send_symmetric_key, b),
            loop.run_in_executor(None, b.recv_symmetric_key),
            loop.run_in_executor(None, c.recv_symmetric_key),
        ))

        # send a msg to Bob
        loop.run_until_complete(asyncio.gather(
            loop.run_in_executor(None, a.send, 0),
            loop.run_in_executor(None, b.validate,),
        ))

        # Forward to Charlie
        loop.run_until_complete(asyncio.gather(
            loop.run_in_executor(None, b.forward_to_charlie,),
            loop.run_in_executor(None, c.validate,),
        ))


if __name__ == "__main__":
    main()
