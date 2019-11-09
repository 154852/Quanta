import quantum as Q

c = Q.Circuit()
A, B = c.create_qubits(2)

# Create |Φ^+> entangled bell state
A.H()
Q.CNOT(A, B)

# Modify state
A.ZX()

# Read state
Q.CNOT(A, B)
A.H()

# Measure state
print("|" + c.M_many(A, B) + "> recieved")