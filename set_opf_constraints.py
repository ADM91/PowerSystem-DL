from copy import deepcopy
import numpy as np


def set_opf_constraints(test_case, branch_deactivated, max_SPA):
    """
    This takes a  test case (with deactivated branches but original generator
    dispatch schedule) and sets the necessary constraints to run opf.

    :param test_case: Matpower case
    :param branch_deactivated: A list of indices to deactivated branches
    :param max_SPA: The maximum standing phase angle constraint on deactivated line
    :return test_case: Modified Matpower case
    """

    # Work with copy of test case
    test_case_opf = deepcopy(test_case)

    # Constrain deactivated branches to max SPA
    for i in branch_deactivated:
        test_case_opf['branch'][i][11:13] = [-max_SPA, max_SPA]

    # Set cost function of each generator as "V" function around scheduled set point
    s = test_case_opf['gencost'].shape
    test_case_opf['gencost'] = np.resize(test_case_opf['gencost'], (s[0], 10))
    for i, gen in enumerate(test_case_opf['gencost']):
        # Model type = piecewise linear
        gen[0] = 1

        # Find set point and max real power for generator i
        set_point = test_case_opf['gen'][i][1]
        max_active = test_case_opf['gen'][i][8]

        # Cost/minimization model
        if set_point > 0:
            # Number of vertices of piecewise model
            gen[3] = 3
            # Set "V" cost function around the scheduled set-point.
            gen[4:] = [0, set_point, set_point, 0, max_active, max_active - set_point]
        else:
            # Number of vertices of piecewise model
            gen[3] = 2
            # Set "V" cost function around the scheduled set-point.
            gen[4:] = [0, 0, max_active, max_active, 0, 0]

    return test_case_opf
