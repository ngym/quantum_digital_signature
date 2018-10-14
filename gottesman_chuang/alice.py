from SimulaQron.cqc.pythonLib.cqc import *
from SimulaQron.quantum_digital_signature.gottesman_chuang.quantum_one_way_function import *
import itertools as it

import numpy as np

def padding0(s, n):
    while len(s) < n:
        s = "0" + s
    return s

def main():
    keylen_per_mbit = 5
    with CQCConnection("Alice") as Alice:
        while True:
            msg = input()
            msg_ascii_binary = [int(i) for i in list(it.chain.from_iterable(
                [padding0(bin(ord(m))[2:], 8) for m in msg]))]
            print("msg_ascii_binary:" + str(msg_ascii_binary))
            msg_len = len(msg_ascii_binary)
            # k: private keys (classical)
            k = []
            for i in range(msg_len):
                k_ = [[], []]
                k_[0] = np.random.randint(0, 2, keylen_per_mbit).tolist()
                k_[1] = np.random.randint(0, 2, keylen_per_mbit).tolist()
                k.append(k_)

            # fket: public keys (quantum)
            fket = []
            for i in range(msg_len):
                fket_ = [[], []]
                fket_[0] = [qubit(Alice) for _ in range(keylen_per_mbit)]
                fket_[1] = [qubit(Alice) for _ in range(keylen_per_mbit)]
                fket.append(fket_)
            for k_, fket_ in zip(k, fket):
                stabilizer_states(k_[0], fket_[0])
                stabilizer_states(k_[1], fket_[1])

            # send
            ## send classical bits
            k_to_send = list(it.chain.from_iterable([k_[m] for k_, m
                                                    in zip(k, msg_ascii_binary)]))
            data = [keylen_per_mbit, msg_len] + msg_ascii_binary + k_to_send

            #print("msg={}".format(msg_ascii_binary))
            #print("k[msg]={}".format(k[msg_ascii_binary]))

            print("data Alice will send:" + repr(data))
            Alice.sendClassical("Bob", data)

            print("Alice send the message msg={} to Bob".format(msg))


            ## send qubits
            for fket_ in fket:
                for q in fket_[0]:
                    Alice.sendQubit(q,"Bob")
                for q in fket_[1]:
                    Alice.sendQubit(q,"Bob")
    

        
main()

