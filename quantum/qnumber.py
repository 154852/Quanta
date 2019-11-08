import quantum as Q
from copy import deepcopy

class QInteger:
    def __init__(self, bits):
        self.l = len(bits)
        self.register = bits

    @staticmethod
    def from_pyint(pyint):
        return QInteger([int(b) for b in list("{0:b}".format(pyint))])

    def add(self, other):
        n = max(other.l, self.l)

        circ = Q.Circuit()
        reg = circ.create_qubits((3 * n) + 1)
        a = reg[0:n]
        b = reg[n:(2 * n) + 1]
        c = reg[(2 * n) + 1:]
        cl = [0 for i in range(n + 1)]

        for idx,i in enumerate(self.register):
            if i == 1:
                a[self.l - (idx + 1)].X()
        
        for idx,i in enumerate(other.register):
            if i == 1:
                b[other.l - (idx + 1)].X()

        for i in range(n - 1):
            Q.CCNOT(a[i], b[i], c[i + 1])
            Q.CNOT(a[i], b[i])
            Q.CCNOT(c[i], b[i], c[i + 1])

        Q.CCNOT(a[n - 1], b[n - 1], b[n])
        Q.CNOT(a[n - 1], b[n - 1])
        Q.CCNOT(c[n - 1], b[n - 1], b[n])
        Q.CNOT(c[n - 1], b[n - 1])

        for i in range(n - 1):
            Q.CCNOT(c[(n - 2) - i], b[(n - 2) - i], c[(n - 1) - i])
            Q.CNOT(a[(n - 2) - i], b[(n - 2) - i])
            Q.CCNOT(a[(n - 2) - i], b[(n - 2) - i], c[(n - 1) - i])

            Q.CNOT(c[(n - 2) - i], b[(n - 2) - i])
            Q.CNOT(a[(n - 2) - i], b[(n - 2) - i])

        for i in range(n + 1):
            cl[n - i] = b[i].M(rtype=int)

        return QInteger(cl)

    def __add__(self, other):
        return self.add(other)

    def to_pyint(self):
        total = 0
        for i,n in enumerate(self.register):
            total += n * (2 ** (self.l - i - 1))

        return total