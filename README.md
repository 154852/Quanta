# Quanta

A quantum computing simulation library, for python.

# How it all works

```python
import quantum as Q

bits = Q.create_register(5)  # Create several bits, all initialised at |0>
A, B, C = Q.create_register(3)

bits[0].X() # Run the first bit of the register through a Pauli-X gate
A.H() # Run this bit through a Hadamard gate
print(A.M()) # Print a true false value for the bit

to_be_entangled = Q.create_register(2)
to_be_entangled[0].H()
Q.CNOT(*to_be_entangled) # Run a CNOT gate on the bits
print(Q.observe_all(*to_be_entangled)) # Will show entangled results (50% 10, 50% 01)

to_be_entangled = Q.create_register(3)
to_be_entangled[0].H()
to_be_entangled[1].X() # Set qubit to 100% 1 state
Q.CCNOT(*to_be_entangled) # Run a CCNOT gate on the bits
print(Q.observe_all(*to_be_entangled)) # Will show entangled results (50% 111, 50% 010)

# The addition on quantum numbers
qint5 = Q.number.QInteger.from_pyint(2)
qint10 = Q.number.QInteger.from_pyint(3)
print((qint5 + qint10).to_pyint())
```

More to come soon!
