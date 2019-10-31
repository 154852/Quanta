import math
import numpy as np

class Matrix(np.ndarray):
    @staticmethod
    def create(data):
        data = np.array(data)
        m = Matrix(data.shape)
        m[:] = data
        return m

    @staticmethod
    def identity(size):
        return Matrix.create(np.identity(size))

    @staticmethod
    def vector(data, vertical):
        data = list(data)

        if vertical: return Matrix.create([[n] for n in data])
        return Matrix.create([data])

    def __mul__(self, other):
        if isinstance(other, Matrix):
            return Matrix.create(self.dot(other))
        elif isinstance(other, np.ndarray):
            return Matrix.create(self.dot(other))
        
        return np.ndarray.__mul__(self, other)