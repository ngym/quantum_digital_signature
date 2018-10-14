from SimulaQron.cqc.pythonLib.cqc import *
from SimulaQron.quantum_digital_signature.gottesman_chuang.quantum_one_way_function import *
import itertools as it

def fredkin(a, b, c):
    # T* = rot_Z(224)
    c.cnot(b)
    c.H()
    a.T()
    b.T()
    c.T()
    b.cnot(a)
    c.cnot(b)
    a.cnot(c)
    b.rot_Z(224)
    c.T()
    a.cnot(b)
    a.rot_Z(224)
    b.rot_Z(224)
    c.cnot(b)
    a.cnot(c)
    b.cnot(a)
    c.H()
    c.cnot(b)

def swap_test(fket, fket_, node):
    assert(len(fket) == len(fket_)), "%d, %d" % (len(fket), len(fket_))
    ret_bitwise = []
    for a, b in zip(fket, fket_):
        q = qubit(node)
        q.H()
        fredkin(q, a, b)
        q.H()
        m = q.measure()
        ret_bitwise.append(m)
    print("ret_bitwise:" + repr(ret_bitwise))
    return sum(ret_bitwise) / len(ret_bitwise)

def main():
    threshold = 0.01
    with CQCConnection("Bob") as Bob:
        while True:
            data = list(Bob.recvClassical())
            print("data Bob received:" + repr(data))
            keylen_per_mbit = data[0]
            msg_len = data[1]
            msg_ascii_binary = data[2:msg_len+2]
            """
            print(msg_ascii_binary)
            msg_ascii_binary[-1] ^= 1
            print(msg_ascii_binary)
            """
            msg = [chr(int(
                "".join([str(m) for m in msg_ascii_binary[i:i+8]]),
                2))
                       for i in range(0, len(msg_ascii_binary), 8)]
            k = data[msg_len+2:]
    
            fket = []
            for _ in range(msg_len):
                fket_ = [[], []]
                for _ in range(keylen_per_mbit):
                    fket_[0].append(Bob.recvQubit())
                for _ in range(keylen_per_mbit):
                    fket_[1].append(Bob.recvQubit())
                fket.append(fket_)
    
            print("Bob retrived the message msg={} from Alice.".format(msg))

            fdashket = []
            fdashket = [qubit(Bob) for _ in range(keylen_per_mbit*msg_len)]
            assert(len(k) == len(fdashket),
                   "%d, %d" % (len(k), len(fdashket)))
            stabilizer_states(k, fdashket)

            fket_to_verify = list(it.chain.from_iterable([fket_[m] for fket_, m in zip(fket, msg_ascii_binary)]))
            retval = swap_test(fket_to_verify, fdashket, Bob)
            #retval = swap_test(fket[0], fdashket, Bob)
    
            if retval < threshold:
                print("valid")
            else:
                print("invalid")
    
main()

