import numpy as np


def SPA_difference(case_result):
    """
    This function takes in a case result and returns the
    standing phase angle (SPA) and voltage magnitude (SVD)
    differences.  Columns of diffs matrix are [voltage, angle].

    :param case_result: the result of a pf simulation
    :return diffs: difference matrix of form [voltage, angle]
    """

    # Number of branches
    n = case_result['branch'].shape[0]

    # Preallocate SPA and SVD difference matrix
    diffs = np.zeros(shape=(n, 2))

    # Loop through branches to get SPA and SVD differences
    for i in range(n):
        # Subtract 1 because we are gathering python indices
        bus1 = int(case_result['branch'][i][0]) - 1
        bus2 = int(case_result['branch'][i][1]) - 1
        diffs[i, :] = case_result['bus'][bus1][7:9] - case_result['bus'][bus2][7:9]

    return diffs
