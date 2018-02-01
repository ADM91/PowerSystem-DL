import numpy as np


def reshape_gencost(gencost):

    # If it doesnt exist return an empty array
    if type(gencost) == list:
        return np.array([])

    # Reshape the gencost matrix to allow piecewise linear objective function
    elif gencost.shape[1] != 9:
        gencost = gencost[:, 0:4]  # Cut off the unnecessary bullshit
        return np.append(gencost, np.zeros((np.shape(gencost)[0], 6)), axis=1)

    # If its already the right shape, return as is
    else:
        return gencost