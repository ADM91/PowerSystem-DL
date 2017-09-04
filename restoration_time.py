import numpy as np


def restoration_time(test_result_dist, test_result_opf, ramp_rates):
    """
    Calculates restoration time of one branch in minutes

    :param test_result_dist: Test case defining base dispatch
    :param test_result_opf: Solution to opf defining target dispatch
    :param ramp_rates: Generator ramp rates (MW/min)
    :return time: Restoration time of targeted branch in minutes
    """
    # Difference in generation dispatch from previous case
    gen_diff = test_result_dist['gen'][:, 1] - test_result_opf['gen'][:, 1]

    # Max time required to ramp
    time = np.max(np.abs(gen_diff/ramp_rates))

    return time
