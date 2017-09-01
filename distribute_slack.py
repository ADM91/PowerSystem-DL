from copy import deepcopy
import numpy as np
from oct2py import octave


def distribute_slack(test_case, base_slack, droop_constants, converge_options, mp_options):
    """
    Redistributes the added slack generation to all generators according to participation factors

    :param test_case: Matpower test case (containing faulted lines)
    :param base_slack: The slack real power generation on the original healthy system
    :param droop_constants: percent droop of each generator
    :param options: convergence options
    :return: test case (faulted lines) with adjusted generation profile, and test results.  Returns
    """
    # Slack bus index
    slack_ind = np.nonzero(test_case['bus'][:, 1] == 3)

    # Normalize droop
    droop_weighted = droop_constants*test_case['gen'][:, 6]
    droop_norm = droop_weighted/np.sum(droop_weighted).reshape((-1, 1))

    # Calculate added slack bus load
    test_result = octave.runpf(test_case, mp_options)
    if test_result['success'] == 0:
        print('Convergence error')
        return False

    slack_diff = test_result['gen'][slack_ind, 1] - base_slack

    # Iterate power flow until convergence or max iteration is reached
    count = 0
    while slack_diff > converge_options['tolerance'] and count <= converge_options['max iteration']:

        # Redistribute slack
        test_case['gen'][:, 1] = test_case['gen'][:, 1] + droop_norm*slack_diff

        # Run power flow
        test_result = octave.runpf(test_case, mp_options)

        # Change in slack output before and after
        slack_diff = test_result['gen'][slack_ind, 1] - test_case['gen'][slack_ind, 1]

        count += 1

    return test_result
