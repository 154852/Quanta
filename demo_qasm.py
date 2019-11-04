from quantum import qasm

DEMO_PROGRAM = """
alloc 4
alloc 3Q(0)
alloc 1b(3)

# Initialise two qubits
# STATE 0Q, 0b
H 0Q
H 1Q
# STATE 1Q, 1b

CCNOT 0Q, 1Q, 2Q

M 2Q, 3b
"""

compiled = qasm.compile_qasm(DEMO_PROGRAM)
print(("-" * 20) + " Compiled Instructions " + ("-" * 20))
print("Completed, instruction count: {}".format(len(compiled)))
print(("-" * 20) + " Executing " + ("-" * 20))

shots = 1000
average = 0
for i in range(shots):
    average += qasm.execute_qasm(compiled).memory[3]

print(average / float(shots))