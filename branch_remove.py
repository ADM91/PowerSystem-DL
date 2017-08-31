import numpy as np


def branch_remove(case, n_branches, branch=-1):
    """
    Removes a random line from the system.
    Specifying a branch will open the branch with the specified index

    :param case: Matpower case
    :param n_branches: number of branches to deactivated
    :param branch: branch index to deactivate
    :return: new case, index to branch(s) to deactivate
    """

    # Number of branches
    n = case['branch'].shape[0]

    # select random integers in range 0 : n-1
    remove = np.random.choice(n, size=n_branches, replace=False)

    # Remove the line(s)
    case['branch'][remove, 10] = 0

    return case, remove








