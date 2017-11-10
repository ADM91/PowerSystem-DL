import numpy as np


def cumulative_lost_load(state_1, state_2, ideal_fixed, ideal_dispatched, time):

    ideal_dispatched = ideal_dispatched.reshape((-1, 1))
    fixed_1 = state_1['fixed load'][:, 1].reshape((-1, 1))
    dispatched_1 = -state_1['dispatch load'][:, 1].reshape((-1, 1))
    dispatched_2 = -state_2['dispatch load'][:, 1].reshape((-1, 1))
    high_load = np.min([ideal_dispatched - dispatched_1, ideal_dispatched - dispatched_2], axis=1)
    low_load = np.max([ideal_dispatched - dispatched_1, ideal_dispatched - dispatched_2], axis=1)

    # Lost dispatchable loads
    lost_d_load = time*(ideal_dispatched - high_load) + 0.5*time*(high_load - low_load)

    # Lost fixed loads
    lost_f_load = time*(ideal_fixed - fixed_1)

    return [lost_d_load, lost_f_load]
