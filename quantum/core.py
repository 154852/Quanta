from math import sqrt, e as euler, pi
from quantum.qmath import *
import random
import numpy as np

def create_register(size):
    reg = Circuit()
    return reg.create_qubits(size)

class State:
    @staticmethod
    def zero(): return Matrix.vector([1, 0], True)

    @staticmethod
    def one(): return Matrix.vector([0, 1], True)

    @staticmethod
    def bool_for(state):
        return state[0,0] == 0 and state[1,0] == 1 and len(state) == 2

    @staticmethod
    def P(state, x):
        return complex_modulus(state[x,0]) ** 2

    @staticmethod
    def create_one_state(size, enabled):
        return Matrix.vector([1 if i == enabled else 0 for i in range(size)], True)

    @staticmethod
    def apply_multi_state(states, *particles):
        for s,state in enumerate(states):
            if state[0] == 1:
                b = "{0:b}".format(s)
                b = ("0" * (len(particles) - len(b))) + b
                for c,char in enumerate(b):
                    particles[c]._set(State.one() if char == "1" else State.zero())

def _observe(arr):
    s = np.sum([(complex_modulus(x) ** 2) for x in arr])
    r = random.uniform(0, s)

    for e,element in enumerate(arr):
        r -= complex_modulus(element[0]) ** 2
        if r <= 0:
            return State.create_one_state(len(arr), e)
    return None

def observe_all(*particles):
    return [p.M() for p in particles]

class Operation:
    XMatrix = Matrix.create([[0, 1], [1, 0]])
    TMatrix = Matrix.create([[1, 0], [0, euler ** ((1j * pi) / 4)]])
    YMatrix = Matrix.create([[0, -1j], [-1j, 0]])
    ZMatrix = Matrix.create([[1, 0], [0, -1]])
    SQRTXMatrix = Matrix.create([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]]) * 0.5
    HMatrix = Matrix.create([[1, 1], [1, -1]]) * (1 / sqrt(2))
    SWAPMatrix = Matrix.create([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    SQRTSWAPMatrix = Matrix.create([[1, 0, 0, 0], [0, 0.5 + 0.5j, 0.5 - 0.5j, 0], [0, 0.5 - 0.5j, 0.5 + 0.5j, 0], [0, 0, 0, 1]])
    CNOTMatrix = Matrix.create([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
    CCNOTMatrix = Matrix.identity(8)
    CSWAPMatrix = Matrix.identity(8)

    @staticmethod
    def create_for_multi_state(matrix, particleCount, index):
        return tensor_product(*[matrix if n == index else Matrix.identity(2) for n in range(particleCount)])

    @staticmethod
    def create_function(name, indices):
        if name is "CNOT": return lambda m, c: Operation.create_wired_CNOT(c, indices[0], indices[1], m)
        if name is "CCNOT": return lambda m, c: Operation.create_wired_CCNOT(c, indices[0], indices[1], indices[2], m)
        
        return lambda m, c: Operation.create_for_multi_state(name, c, indices[0]) * m

    @staticmethod
    def create_wired_CNOT(particleCount, controlIndex, targetIndex, m):
        a = tensor_product(*[(State.zero().projection() if n == controlIndex else Matrix.identity(2)) for n in range(particleCount)])
        b = tensor_product(*[(State.one().projection() if n == controlIndex else (Operation.XMatrix if n == targetIndex else Matrix.identity(2))) for n in range(particleCount)])
        return (a + b) * m

    @staticmethod
    def create_wired_CCNOT(particleCount, control1Index, control2Index, targetIndex, m):
        m = Operation.create_for_multi_state(Operation.HMatrix, particleCount, targetIndex) * m
        m = Operation.create_wired_CNOT(particleCount, control2Index, targetIndex, m)
        m = Operation.create_for_multi_state(Operation.TMatrix.conjuagte_transpose(), particleCount, targetIndex) * m
        m = Operation.create_wired_CNOT(particleCount, control1Index, targetIndex, m)
        m = Operation.create_for_multi_state(Operation.TMatrix, particleCount, targetIndex) * m
        m = Operation.create_wired_CNOT(particleCount, control2Index, targetIndex, m)
        m = Operation.create_for_multi_state(Operation.TMatrix.conjuagte_transpose(), particleCount, targetIndex) * m
        m = Operation.create_wired_CNOT(particleCount, control1Index, targetIndex, m)
        m = Operation.create_for_multi_state(Operation.TMatrix, particleCount, control2Index) * m
        m = Operation.create_for_multi_state(Operation.TMatrix, particleCount, targetIndex) * m
        m = Operation.create_for_multi_state(Operation.HMatrix, particleCount, targetIndex) * m
        m = Operation.create_wired_CNOT(particleCount, control1Index, control2Index, m)
        m = Operation.create_for_multi_state(Operation.TMatrix, particleCount, control1Index) * m
        m = Operation.create_for_multi_state(Operation.TMatrix.conjuagte_transpose(), particleCount, control2Index) * m
        m = Operation.create_wired_CNOT(particleCount, control1Index, control2Index, m)
        return m

Operation.CCNOTMatrix[6,6] = 0
Operation.CCNOTMatrix[7,6] = 1
Operation.CCNOTMatrix[7,7] = 0
Operation.CCNOTMatrix[6,7] = 1

Operation.CSWAPMatrix[5,5] = 0
Operation.CSWAPMatrix[5,6] = 1
Operation.CSWAPMatrix[6,5] = 1
Operation.CSWAPMatrix[6,6] = 0

class Qubit:
    def __init__(self, c, state=None):
        self.state = state or State.zero()
        self.circuit = c

    @staticmethod
    def create_one(state=None):
        circuit = Circuit()
        bit = circuit.create_qubits(1)[0]
        if state is not None: bit._set(state)
        return bit

    def H(self): self.circuit.H(self)
    def X(self): self.circuit.X(self)
    def Y(self): self.circuit.Y(self)
    def Z(self): self.circuit.Z(self)
    def SQRTX(self): self.circuit.SQRTX(self)
    def ZX(self): self.circuit.ZX(self)
    def M(self, rtype=bool): return self.circuit.M(self, rtype)

    def _set(self, state): self.state = state

class BellState:
    @staticmethod
    def phip(p1, p2, c):
        c.H(p1)
        c.CNOT(p1, p2)

    @staticmethod
    def phim(p1, p2, c):
        BellState.phip(p1, p2, c)
        c.Z(p1)

    @staticmethod
    def psip(p1, p2, c):
        BellState.phip(p1, p2, c)
        c.X(p1)

    @staticmethod
    def psim(p1, p2, c):
        BellState.phip(p1, p2, c)
        c.ZX(p1)

class EntanglementStep:
    def __init__(self, particles, functions=None):
        self.particles = particles
        self.functions = functions or []

    def add(self, name, *indices):
        self.functions.append(StepFunction(name, indices))

    def merge(self, step2):
        current_size = len(self.particles)
        for f in step2.functions: f.offset(current_size)
        self.particles.extend(step2.particles)
        self.functions.extend(step2.functions)

    def execute(self):
        state = tensor_product(*[p.state for p in self.particles])
        for f in self.functions:
            state = f.create()(state, len(self.particles))
            assert state.shape == (2 ** len(self.particles), 1)

        state = _observe(state)
        State.apply_multi_state(state, *self.particles)

class StepFunction:
    def __init__(self, name, indices):
        self.name = name
        self.indices = indices

    def offset(self, o):
        self.indices = [i + o for i in self.indices]
    
    def create(self):
        return Operation.create_function(self.name, self.indices)

def _observe(arr):
    s = np.sum([(complex_modulus(x) ** 2) for x in arr])
    r = random.uniform(0, s)

    for e,element in enumerate(arr):
        r -= complex_modulus(element[0]) ** 2
        if r <= 0:
            return State.create_one_state(len(arr), e)
    return None

class Circuit:
    def __init__(self):
        self.qubits = []
        self.entanglement_steps = []

    def create_qubits(self, bits):
        bits = [Qubit(self) for _ in range(bits)]
        self.qubits.extend(bits)
        return tuple(bits)

    def extend_matrix(self, qubits, label):
        if not isinstance(qubits, list): qubits = [qubits]

        included = []
        for step in self.entanglement_steps:
            for q in qubits:
                if q in step.particles and step not in included:
                    included.append(step)

        if len(included) != 0:
            step = included[0]
            for i in range(1, len(included), 1):
                step.merge(included[i])
                self.entanglement_steps.remove(included[i])

            for q in qubits:
                if not q in step.particles:
                    step.particles.append(q)

            step.add(label, *[step.particles.index(p) for p in qubits])
        else:
            if len(qubits) == 1: qubits[0].state = label * qubits[0].state
            else:
                step = EntanglementStep(qubits)
                step.add(label, *list(range(len(qubits))))
                self.entanglement_steps.append(step)

    def H(self, qubit): self.extend_matrix(qubit, Operation.HMatrix)

    def Z(self, qubit): self.extend_matrix(qubit, Operation.ZMatrix)
    def X(self, qubit): self.extend_matrix(qubit, Operation.XMatrix)
    def Y(self, qubit): self.extend_matrix(qubit, Operation.YMatrix)
    def SQRTX(self, qubit): self.extend_matrix(qubit, Operation.SQRTXMatrix)
    def ZX(self, qubit): self.extend_matrix(qubit, Operation.ZMatrix * Operation.XMatrix)
    def CNOT(self, qubit1, qubit2): self.extend_matrix([qubit1, qubit2], "CNOT")
    def CCNOT(self, qubit1, qubit2, qubit3): self.extend_matrix([qubit1, qubit2, qubit3], "CCNOT")

    def M(self, qubit, rtype=bool):
        for e in self.entanglement_steps:
            if qubit in e.particles:
                e.execute()
                self.entanglement_steps.remove(e)

        qubit.state = _observe(qubit.state)
        if rtype == Matrix: return qubit.state
        if rtype == bool: return State.bool_for(qubit.state)
        return int(State.bool_for(qubit.state))

    def M_many(self, *bits):
        return "".join([str(self.M(b, int)) for b in bits])

def CNOT(qubit1, qubit2): qubit1.circuit.CNOT(qubit1, qubit2)
def CCNOT(qubit1, qubit2, qubit3): qubit1.circuit.CCNOT(qubit1, qubit2, qubit3)