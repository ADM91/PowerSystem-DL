import numpy as np


def delay_faulty_action(sequence, violation_ind):

    # Swap faulty action with random sequential point
    a = violation_ind
    try:
        b = np.random.randint(low=a+1, high=len(sequence)-1)
        if b < len(sequence):
            sequence[a], sequence[b] = sequence[b], sequence[a]
    except ValueError:
        pass

    return sequence

