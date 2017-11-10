import numpy as np


def ramp_time(state_1, state_2, ramp_rates):
    """
    Calculates restoration time of one branch in minutes

    :param state_1: Test case defining base dispatch
    :param state_2: Solution to opf defining target dispatch
    :param ramp_rates: Generator ramp rates (MW/min)
    :return time: Restoration time of targeted branch in minutes
    """

    # Difference in generation dispatch from previous case
    gen_diff = state_2['real gen'][:, 1] - state_1['real gen'][:, 1]

    # Time required to ramp
    time = np.abs(gen_diff/ramp_rates)

    return np.max(time)
