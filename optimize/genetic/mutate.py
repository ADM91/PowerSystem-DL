import numpy as np


def mutate(children, n_mutations):

    n, m = children.shape

    for child in children:
        for i in range(n_mutations):
            s1 = int(np.random.choice(m))
            s2 = int(np.random.choice(m))
            child[[s1, s2]] = child[[s2, s1]]

    return children
