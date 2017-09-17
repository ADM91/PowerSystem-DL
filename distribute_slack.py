from copy import deepcopy
import numpy as np
from oct2py import octave
from config import mp_opt


def distribute_slack(case, droop_constants, converge_options):
    """
    Redistributes the added slack generation to all generators according to participation factors

    :param case: Matpower test case (containing faulted lines)
    :param slack_ind: Index to the slack bus
    :param droop_constants: percent droop of each generator
    :param converge_options: convergence options
    :return test_result_dist: test case result (faulted lines) with adjusted generation profile
    """

    slack_ind = case['slack_ind']

    # Copy of test case worked with
    case_distr = deepcopy(case)

    # Original power generated at slack bus
    base_slack = case['gen'][slack_ind, 1]

    # Normalize droop
    droop_weighted = droop_constants*case['gen'][:, 6]
    droop_norm = droop_weighted/np.sum(droop_weighted).reshape((-1, 1))

    # Calculate added slack bus load
    test_result_dist = octave.runpf(case_distr, mp_opt)

    # Return if power flow does not converge
    if test_result_dist['success'] == 0:
        print('Convergence error')
        return False

    slack_diff = test_result_dist['gen'][slack_ind, 1] - base_slack

    # Iterate power flow until convergence or max iteration is reached
    count = 0
    while slack_diff > converge_options['tolerance'] and count <= converge_options['max iteration']:

        # Redistribute slack
        case_distr['gen'][:, 1] = case_distr['gen'][:, 1] + droop_norm*slack_diff

        # Run power flow
        test_result_dist = octave.runpf(case_distr, mp_opt)

        # Change in slack output before and after
        slack_diff = test_result_dist['gen'][slack_ind, 1] - case_distr['gen'][slack_ind, 1]

        count += 1

    return test_result_dist
