import numpy as np


def action_time(state_1, state_2, ramp_rates):
    """
    Calculates restoration time of one branch in minutes

    :param state_1: Test case defining base dispatch
    :param state_2: Solution to opf defining target dispatch
    :param ramp_rates: Generator ramp rates (MW/min)
    :return time: Restoration time of targeted branch in minutes
    """

    # Power difference between cases
    gen_diff = state_2['real gen'][:, 1] - state_1['real gen'][:, 1]
    f_load_diff = state_2['fixed load'][:, 1] - state_1['fixed load'][:, 1]
    d_load_diff = state_2['dispatch load'][:, 1] - state_1['dispatch load'][:, 1]

    # Time required to achieve changes
    gen_time = np.abs(gen_diff/ramp_rates)   # Ramp rate 10 MW/min
    f_load_time = np.abs(f_load_diff*0.02)  # 0.02 min/MW (1.2 sec/MW)
    d_load_time = np.abs(d_load_diff*0.02)  # 0.02 min/MW (1.2 sec/MW)

    # Add 15 sec of mechanical/operator delay time per action
    total = 0.25 + np.max([np.max(gen_time), np.max(f_load_time), np.max(d_load_time)])

    return total
