# Quanta

A quantum computing simulation library, for python.

# How it all works

```python
import quantum as Q

bit = Q.Qubit() # Create one bit, initialised at |0>
bit = Q.Qubit(Q.State.one()) # Create one bit, initialised at |1>
several_bits = Q.create_register(5)  # Create several bits, all initialised at |0> (this is just an array)

several_bits[0].X() # Run the first bit of the register through a Pauli-X gate
bit.H() # Run this bit through a Hadamard gate
print(bit.M()) # Print a true false value for the bit

to_be_entangled = Q.create_register(2)
to_be_entangled[0].H()
Q.CNOT(*to_be_entangled) # Run a CNOT gate on the bits
print(Q.observe_all(*to_be_entangled)) # Will show entangled results (50% 10, 50% 01)

to_be_entangled = Q.create_register(3)
to_be_entangled[0].H()
to_be_entangled[1].set(Q.State.one()) # Set qubit to 100% 1 state
Q.CCNOT(*to_be_entangled) # Run a CCNOT gate on the bits
print(Q.observe_all(*to_be_entangled)) # Will show entangled results (50% 111, 50% 010)

# To addition on quantum numbers
qint5 = Q.number.QInteger.from_pyint(5)
qint10 = Q.number.QInteger.from_pyint(10)
print((qint5 + qint10).to_pyint())
```

More to come soon!