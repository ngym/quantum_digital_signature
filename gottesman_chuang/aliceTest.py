from SimulaQron.cqc.pythonLib.cqc import *
from SimulaQron.quantum_digital_signature.gottesman_chuang.quantum_one_way_function import *

import numpy as np

def main():
    keylen_per_mbit = 5
    msg_len = 1
    msg = np.random.randint(0, 2, msg_len)
    msg = 1
    with CQCConnection("Alice") as Alice:
        data = [keylen_per_mbit, msg_len]
        Alice.sendClassical("Bob", data)
        
        # k: private keys (classical)
        k = [[], []]
        k[0] = np.random.randint(0, 2, keylen_per_mbit).tolist()
        k[1] = np.random.randint(0, 2, keylen_per_mbit).tolist()

        # fket: public keys (quantum)
        fket = [[], []]
        fket[0] = [qubit(Alice) for _ in range(keylen_per_mbit)]
        fket[1] = [qubit(Alice) for _ in range(keylen_per_mbit)]

        stabilizer_states(k[0], fket[0])
        stabilizer_states(k[1], fket[1])

        # send
        ## send qubits
        for q in fket[0]:
            Alice.sendQubit(q,"Bob")
        for q in fket[1]:
            Alice.sendQubit(q,"Bob")

        ## send classical bits
        print("msg={}".format(msg))
        print("k[msg]={}".format(k[msg]))
        data = [msg] + k[msg]
        print("data Alice will send:" + repr(data))
        Alice.sendClassical("Bob", data)

        print("Alice send the message msg={} to Bob".format(msg))
        
main()

