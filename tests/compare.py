import numpy as np
from scipy.sparse import coo_matrix


def proc_attr(proc_or_array, attr) -> list:
    if hasattr(proc_or_array, attr):
        x = getattr(proc_or_array, attr)
        if callable(x):
            return x()
        else:
            return x
    else:
        return proc_or_array


def neuron_vectors_sparse(arr_or_proc):
    neuron_vectors = proc_attr(arr_or_proc, "neuron_vectors")
    ones, (row, col) = np.array([
        (1, t, int(v))
        for t, vec in enumerate(neuron_vectors)
        for v in vec]).T
    return coo_matrix((ones, (row, col)))


def neuron_vectors_dense(arr_or_proc, max_t):
    neuron_vectors = proc_attr(arr_or_proc, "neuron_vectors")
    if max_t is None:
        max_t = max(max(vec) for vec in neuron_vectors)
    arr = np.zeros((len(neuron_vectors), max_t + 1))
    for t, vec in enumerate(neuron_vectors):
        for v in vec:
            arr[t, v] = 1
    return arr


def compare(caspian_proc, caspyan_proc, max_t=None, print_diff=True):
    caspian_counts = np.array(caspian_proc.neuron_counts())
    caspyan_counts = np.array(caspyan_proc.neuron_counts())
    counts_match = np.array_equiv(caspyan_counts, caspian_counts)

    caspian_vectors = neuron_vectors_dense(caspian_proc, max_t)
    caspyan_vectors = neuron_vectors_dense(caspyan_proc, max_t)
    vectors_match = np.array_equiv(caspyan_vectors, caspian_vectors)

    caspian_charges = np.array(caspian_proc.neuron_charges())
    caspyan_charges = np.array(caspyan_proc.neuron_charges())
    charges_match = np.array_equiv(caspyan_charges, caspian_charges)

    def prnt(*args, **kwargs):
        if print_diff:
            print(*args, **kwargs)

    if not counts_match:
        prnt(f"neuron counts do not match")
        prnt(f"caspian: {caspian_counts}")
        prnt(f"caspyan: {caspyan_counts}")

    if not vectors_match:
        for t, cpvec, pyvec in enumerate(zip(caspian_vectors, caspyan_vectors)):
            if not np.array_equiv(cpvec, pyvec):
                prnt(f"neuron counts at t={t} do not match")
                prnt(f"caspian: {cpvec}")
                prnt(f"caspyan: {pyvec}")

    if not charges_match:
        prnt(f"neuron charges do not match")
        prnt(f"caspian: {caspian_charges}")
        prnt(f"caspyan: {caspyan_charges}")

    return counts_match and vectors_match and charges_match
