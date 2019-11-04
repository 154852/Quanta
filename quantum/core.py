from math import sqrt, e as euler
from quantum.qmath import *
import random
import numpy as np

def complex_modulus(c):
    return sqrt((c.real ** 2) + (c.imag ** 2))

def prod(arr):
    p = 1
    for item in arr: p *= item
    return p

class State:
    @staticmethod
    def zero(): return Matrix.vector([1, 0], True)

    @staticmethod
    def one(): return Matrix.vector([0, 1], True)

    @staticmethod
    def create_one_state(size, enabled):
        return Matrix.vector([1 if i == enabled else 0 for i in range(size)], True)

    @staticmethod
    def bool_for(state):
        return state[0,0] == 0 and state[1,0] == 1 and len(state) == 2

    @staticmethod
    def P(state, x):
        return complex_modulus(state[x,0]) ** 2

    @staticmethod
    def from_particles(*particles):
        arr = [0 for i in range(2 ** len(particles))]
        for i in range(len(arr)):
            probs = "{0:b}".format(i)
            probs = ("0" * (len(particles) - len(probs))) + probs

            arr[i] = sqrt(prod([particles[n].P(int(probs[n])) for n in range(len(particles))]))

        return Matrix.vector(arr, True)

    @staticmethod
    def apply_multi_state(states, *particles):
        for s,state in enumerate(states):
            if state[0] == 1:
                b = "{0:b}".format(s)
                b = ("0" * (len(particles) - len(b))) + b
                for c,char in enumerate(b):
                    particles[c].set(State.one() if char == "1" else State.zero())

def create_register(size):
    return [Qubit(None) for _ in range(size)]

def observe_all(*particles):
    return [p.M() for p in particles]

def _observe(arr):
    s = np.sum([(complex_modulus(x) ** 2) for x in arr])
    r = random.uniform(0, s)

    for e,element in enumerate(arr):
        r -= complex_modulus(element[0]) ** 2
        if r <= 0:
            return State.create_one_state(len(arr), e)
    return None

class Operation:
    XMatrix = Matrix.create([[0, 1], [1, 0]])
    YMatrix = Matrix.create([[0, -1j], [-1j, 0]])
    ZMatrix = Matrix.create([[1, 0], [0, -1]])
    SQRTXMatrix = Matrix.create([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]]) * 0.5
    HMatrix = Matrix.create([[1, 1], [1, -1]]) * (1 / sqrt(2))
    SWAPMatrix = Matrix.create([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    SQRTSWAPMatrix = Matrix.create([[1, 0, 0, 0], [0, 0.5 + 0.5j, 0.5 - 0.5j, 0], [0, 0.5 - 0.5j, 0.5 + 0.5j, 0], [0, 0, 0, 1]])
    CNOTMatrix = Matrix.create([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
    CCNOTMatrix = Matrix.identity(8)
    CSWAPMatrix = Matrix.identity(8)

    def get_all():
        v = vars(Operation)
        return [(p[0:-len("Matrix")], int(math.log2(v[p].shape[0]))) for p in v.keys() if p.endswith("Matrix")]

Operation.CCNOTMatrix[6,6] = 0
Operation.CCNOTMatrix[7,6] = 1
Operation.CCNOTMatrix[7,7] = 0
Operation.CCNOTMatrix[6,7] = 1

Operation.CSWAPMatrix[5,5] = 0
Operation.CSWAPMatrix[5,6] = 1
Operation.CSWAPMatrix[6,5] = 1
Operation.CSWAPMatrix[6,6] = 0

class Qubit:
    def __init__(self, initial):
        self.initial = State.zero() if initial is None else initial
        self.state = self.initial
    
    def H(self): _operate(Operation.HMatrix, self)
    def X(self): _operate(Operation.XMatrix, self)
    def Y(self): -operate(Operation.YMatrix, self)
    def Z(self): _operate(Operation.ZMatrix, self)
    def SQRTX(self): _operate(Operation.SQRTXMatrix, self)
    def R(self, phi): _operate(Matrix.create([[1, 0], [0, euler ** (phi * 1j)]]), self)
    
    def P(self, n): return complex_modulus(self.state[n,0]) ** 2
    
    def M(self):
        self.state = _observe(self.state)
        return State.bool_for(self.state)

    def set(self, state): self.state = state

def _operate(matrix, *particles):
    if matrix.shape[0] == 2:
        particles[0].state = matrix * particles[0].state
    else:
        full = State.from_particles(*particles)
        full = matrix * full
        full = _observe(full) # This, admittedly is cheating. it means that the state vector will no longer hold the true probabilities of different
        # outomes.

        # Realistically, this is not what happens, instead a kind of tree of probabilities should be constructed, where every eventual outcome
        # has a branch and a probability associated with it. However, at some point the choice will have to be made, for example between one of
        # |00>, |01>, |10>, |11>, so we lose no accuracy or realism by simply making this choice early, after all a mental war was fought
        # over whether this actually happens by Einstein and Bohr, and some QM interpretations rely on hidden variables to let the choice be made early. 
        # Doing it this way is simply a shortcut for us. There would an issue in that if multiple observations were made, only certain outcomes 
        # could ever be gained, but in a realistic quantum computer, an oberservation is irreversible anyway, so this is not an issue.
        State.apply_multi_state(full, *particles)

def CNOT(a, b): _operate(Operation.CNOTMatrix, a, b)
def CCNOT(a, b, c): _operate(Operation.CCNOTMatrix, a, b, c)
def CSWAP(a, b, c): _operate(Operation.CSWAPMatrix, a, b, c)