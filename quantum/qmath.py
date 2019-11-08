import math
import numpy as np

def complex_modulus(c):
    return math.sqrt((c.real ** 2) + (c.imag ** 2))

def prod(arr):
    p = 1
    for item in arr: p *= item
    return p

def tensor_product(*args):
    mat = np.kron(args[0], args[1])
    for i in range(len(args) - 2): mat = np.kron(mat, args[i + 2])
    return mat

class Matrix(np.ndarray):
    @staticmethod
    def create(data):
        data = np.array(data)
        m = Matrix(data.shape, dtype="complex128")
        m[:] = data
        return m

    @staticmethod
    def identity(size):
        return Matrix.create(np.identity(size))

    @staticmethod
    def vector(data, vertical=False):
        data = list(data)

        if vertical: return Matrix.create([[n] for n in data])
        return Matrix.create([data])

    def projection(self):
        return self * np.transpose(self)

    def conjuagte_transpose(self):
        return np.transpose(self).conj()

    def __mul__(self, other):
        if isinstance(other, Matrix):
            return Matrix.create(self.dot(other))
        elif isinstance(other, np.ndarray):
            return Matrix.create(self.dot(other))
        
        return np.ndarray.__mul__(self, other)