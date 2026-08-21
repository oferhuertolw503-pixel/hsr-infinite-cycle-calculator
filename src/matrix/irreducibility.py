"""Irreducibility checks via strongly connected components.

Perron-Frobenius strict positivity (theory document theorems 2 and 3)
requires the transfer matrix to be irreducible.  A non-negative matrix
is irreducible iff its directed graph -- edge i -> j when A[i, j] > 0 --
is strongly connected.
"""

import numpy as np


def strongly_connected_components(matrix, eps=1e-12):
    """Return the strongly connected components of the digraph of `matrix`.

    Iterative Tarjan's algorithm; components are lists of node indices.
    Edge i -> j exists iff matrix[i, j] > eps.
    """
    A = np.asarray(matrix, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("matrix must be square")
    n = A.shape[0]
    if n == 0:
        return []

    adj = [[j for j in range(n) if A[i, j] > eps] for i in range(n)]

    index = [-1] * n
    lowlink = [0] * n
    on_stack = [False] * n
    stack = []
    counter = [0]
    result = []

    for root in range(n):
        if index[root] != -1:
            continue
        frames = [(root, 0)]
        while frames:
            v, pi = frames[-1]
            if pi == 0:
                index[v] = lowlink[v] = counter[0]
                counter[0] += 1
                stack.append(v)
                on_stack[v] = True
            if pi < len(adj[v]):
                w = adj[v][pi]
                frames[-1] = (v, pi + 1)
                if index[w] == -1:
                    frames.append((w, 0))
                elif on_stack[w]:
                    lowlink[v] = min(lowlink[v], index[w])
            else:
                frames.pop()
                if frames:
                    parent = frames[-1][0]
                    lowlink[parent] = min(lowlink[parent], lowlink[v])
                if lowlink[v] == index[v]:
                    component = []
                    while True:
                        w = stack.pop()
                        on_stack[w] = False
                        component.append(w)
                        if w == v:
                            break
                    result.append(component)
    return result


def is_irreducible(matrix, eps=1e-12):
    """True iff the digraph of the matrix is strongly connected."""
    A = np.asarray(matrix, dtype=float)
    if A.shape[0] == 0:
        return True
    return len(strongly_connected_components(A, eps=eps)) == 1


def condensation_summary(matrix, node_names=None, eps=1e-12):
    """Summarize the strongly connected components of the matrix graph."""
    n = np.asarray(matrix).shape[0]
    if node_names is None:
        node_names = [f"x{i}" for i in range(n)]
    components = strongly_connected_components(matrix, eps=eps)
    return [
        {
            "nodes": sorted(comp),
            "names": [node_names[i] for i in sorted(comp)],
        }
        for comp in components
    ]
