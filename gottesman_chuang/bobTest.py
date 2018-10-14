from SimulaQron.cqc.pythonLib.cqc import *
from SimulaQron.quantum_digital_signature.gottesman_chuang.quantum_one_way_function import *

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
        data = list(Bob.recvClassical())
        print("data Bob received:" + repr(data))
        keylen_per_mbit = data[0]
        msg_len = data[1]

        fket = [[], []]
        for _ in range(msg_len * keylen_per_mbit):
            fket[0].append(Bob.recvQubit())
        for _ in range(msg_len * keylen_per_mbit):
            fket[1].append(Bob.recvQubit())

        data = list(Bob.recvClassical())
        print("data Bob received:" + repr(data))
        msg = data[:msg_len]
        k = data[msg_len:]

        fdashket = [qubit(Bob) for _ in range(keylen_per_mbit)]
        stabilizer_states(k, fdashket)

        retval = swap_test(fket[msg[0]], fdashket, Bob)
        #retval = swap_test(fket[0], fdashket, Bob)

        if retval < threshold:
            print("valid")
        else:
            print("invalid")

        print("Bob retrived the message msg={} from Alice.".format(msg))

main()

