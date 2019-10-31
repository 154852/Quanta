from math import sqrt
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
        return state[x,0] ** 2

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
    s = np.sum([(x ** 2) for x in arr])
    r = random.uniform(0, s)

    for e,element in enumerate(arr):
        r -= element[0] ** 2
        if r <= 0:
            return State.create_one_state(len(arr), e)
    return None

class Operation:
    XMatrix = Matrix.create([[0, 1], [1, 0]])
    HMatrix = Matrix.create([[1, 1], [1, -1]]) * (1 / sqrt(2))
    CNOTMatrix = Matrix.create([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
    CCNOTMatrix = Matrix.identity(8)

Operation.CCNOTMatrix[6,6] = 0
Operation.CCNOTMatrix[7,6] = 1
Operation.CCNOTMatrix[7,7] = 0
Operation.CCNOTMatrix[6,7] = 1

class Qubit:
    def __init__(self, initial):
        self.initial = State.zero() if initial is None else initial
        self.state = self.initial

    def X(self):
        self.state = Operation.XMatrix * self.state
    
    def H(self):
        self.state = Operation.HMatrix * self.state

        
    @staticmethod
    def CNOT(a, b):
        return CNOT(a, b)

    @staticmethod
    def CCNOT(a, b, c):
        return CCNOT(a, b, c)
    
    def P(self, n):
        return self.state[n,0] ** 2
    
    def M(self):        
        return State.bool_for(_observe(self.state))

    def set(self, state):
        self.state = state


def CNOT(a, b):
    full = State.from_particles(a, b)
    full = Operation.CNOTMatrix * full
    full = _observe(full)

    State.apply_multi_state(full, a, b)

def CCNOT(a, b, c):
    full = State.from_particles(a, b, c)
    full = Operation.CCNOTMatrix * full
    full = _observe(full)

    State.apply_multi_state(full, a, b, c)