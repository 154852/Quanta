import quantum as Q

c = Q.Circuit()
A, B, C, D = c.create_qubits(4)

B.H()
Q.CNOT(A, B)

Q.CNOT(C, D)

Q.CNOT(B, C)

pass