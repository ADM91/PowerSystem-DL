import numpy as np
from copy import copy


def cumulative_lost_load(state_1, state_2, ideal_fixed, ideal_dispatched, time):

    ideal_fixed = ideal_fixed.reshape((-1, 1))
    ideal_dispatched = ideal_dispatched.reshape((-1, 1))
    fixed_2 = copy(state_2['fixed load'][:, 1].reshape((-1, 1)))
    dispatched_1 = np.nan_to_num(copy(-state_1['dispatch load'][:, 1].reshape((-1, 1))))
    dispatched_2 = np.nan_to_num(copy(-state_2['dispatch load'][:, 1].reshape((-1, 1))))
    high_lost_load = np.min([ideal_dispatched - dispatched_1, ideal_dispatched - dispatched_2], axis=0)
    low_lost_load = np.max([ideal_dispatched - dispatched_1, ideal_dispatched - dispatched_2], axis=0)

    # Lost dispatchable loads
    mean_d_load = np.mean([low_lost_load, high_lost_load], axis=0)
    lost_d_load = time*mean_d_load

    # Lost fixed loads
    lost_f_load = time*(ideal_fixed - fixed_2)

    return [lost_d_load, lost_f_load]

