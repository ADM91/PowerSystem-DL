from copy import deepcopy
import numpy as np
from oct2py import octave


def set_opf_constraints(test_case_opf, set_branch=[], max_SPA=365, set_gen=True, set_loads=False):
    """
    This takes a  test case (with deactivated branches but original generator
    dispatch schedule) and sets the necessary constraints to run opf.

    :param test_case: Matpower case
    :param branch_deactivated: A list of indices to deactivated branches
    :param max_SPA: The maximum standing phase angle constraint on deactivated line
    :return test_case: Modified Matpower case
    """

    # Work with copy of test case
    # test_case_opf = deepcopy(test_case)

    # Reshape the gencost matrix to allow piecewise linear cost function
    test_case_opf['gencost'] = test_case_opf['gencost'][:, 0:4]
    test_case_opf['gencost'] = np.append(test_case_opf['gencost'], np.zeros((np.shape(test_case_opf['gencost'])[0], 6)), axis=1)

    if set_branch:
        # Constrain deactivated target branch to max SPA
        test_case_opf['branch'][set_branch][11:13] = [-max_SPA, max_SPA]

    if set_loads:

        # Make loads curtailable/dispatchable
        # first find loads in the case
        load_ind = test_case_opf['bus'][:, 2] > 0
        load_bus = test_case_opf['bus'][load_ind, 0]
        real_loads = test_case_opf['bus'][load_ind, 2]
        react_loads = test_case_opf['bus'][load_ind, 3]

        # Set loads in the bus matrix to zero
        test_case_opf['bus'][:, 2:4] = 0

        # Represent loads as negative generators!
        for i in range(len(load_bus)):
            # Gen setup: BUS, PG, QG, Qmax, Qmin, VG, MBASE, STATUS, PMAX, PMIN
            new_gen = [load_bus[i],
                       -real_loads[i],
                       -react_loads[i],
                       np.max([0, -react_loads[i]]),
                       np.min([0, -react_loads[i]]),
                       1,
                       test_case_opf['baseMVA'],
                       1,
                       0,
                       -real_loads[i]]
            new_gen = np.append(new_gen, 11*[0]).reshape((1, -1))

            # Append dispatchable load to gen matrix
            test_case_opf['gen'] = np.append(test_case_opf['gen'], new_gen, axis=0)

            # Append dispatchable load to gencost matrix
            new_gencost = np.array([1, 0, 0, 2, -real_loads[i], -real_loads[i], 0, 0, 0, 0]).reshape((1,-1))
            test_case_opf['gencost'] = np.append(test_case_opf['gencost'], new_gencost, axis=0)

            # Two endpoints of gencost function
            test_case_opf['gencost'][-1, 3] = 2

    if set_gen:
        # Set cost function of each non-load generator as "V" function around scheduled set point
        # s = test_case_opf['gencost'].shape
        # test_case_opf['gencost'] = np.resize(test_case_opf['gencost'], (s[0], 10))

        # Which generators are real? Only loop over the real ones
        legit_gen = octave.isload(test_case_opf['gen'])

        if type(legit_gen) == int: legit_gen = [legit_gen,]

        for i, gen in enumerate(test_case_opf['gencost']):

            # Only perform on non-load generators
            if legit_gen[i] == 0:
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
            else:
                continue

    return test_case_opf
