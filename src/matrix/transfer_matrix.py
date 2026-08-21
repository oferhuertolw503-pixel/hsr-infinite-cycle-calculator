"""Resource transfer matrix engine."""

import numpy as np


class TransferMatrix:
    def __init__(self, matrix):
        self.A = np.asarray(matrix, dtype=float)

    def spectral_radius(self):
        values = np.linalg.eigvals(self.A)
        return float(np.max(np.abs(values)))

    def eigen_analysis(self):
        values, vectors = np.linalg.eig(self.A)
        index = np.argmax(np.abs(values))
        return values[index], vectors[:, index]


if __name__ == "__main__":
    model = TransferMatrix([[0, 1], [0.5, 0]])
    print(model.spectral_radius())
