import numpy as np


def mutate(children, eta):

    n, m = children.shape

    for child in children:
        r = np.random.rand()
        if r < eta:
            flag = np.random.rand()
            s1 = int(np.random.choice(m))
            s2 = int(np.random.choice(m))
            child[[s1, s2]] = child[[s2, s1]]

    return children

