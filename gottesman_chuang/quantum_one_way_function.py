def stabilizer_states(cbits, qubits):
    for c,q in zip(cbits, qubits):
        if c == 0:
            pass
        else:
            q.H()

            
