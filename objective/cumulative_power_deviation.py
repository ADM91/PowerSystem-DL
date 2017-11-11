import numpy as np


def cumulative_power_deviation(base_dispatch, state_1, state_2, ramp_time):
    """
    Solves for the sum deviation from base case generator schedule during the ramping
    period prior to reconnection.  Units come out to MW*min.

    :param base_dispatch: The scheduled generator dispatch
    :param state_1: The initial generator dispatch
    :param state_2: The target generator dispatch
    :param ramp_time: Time taken to ramp all generators (minutes)
    :return: Cumulative energy deviated from the base schedule (MW*minute)
    """

    # Base dispatch
    base_dispatch = base_dispatch.reshape((-1, 1))

    # Initial dispatch
    initial = state_1['real gen'][:, 1].reshape((-1, 1))

    # Final dispatch
    final = state_2['real gen'][:, 1].reshape((-1, 1))

    # Calculate sum of dispatch deviation
    # need to find if the base straddles the initial and final states
    mi = np.min([initial, final], axis=0)
    ma = np.max([initial, final], axis=0)
    si = np.logical_and(base_dispatch > mi, base_dispatch < ma).reshape((-1, 1))  # straddle index array (si)

    # Length (min) of triangles straddling the base
    w1 = ramp_time/(1 + np.abs(base_dispatch[si]-ma[si])/np.abs(base_dispatch[si]-mi[si]))
    w2 = ramp_time - w1

    # Cumulative deviation of the generators straddling the base dispatch
    deviation_si = w1*(base_dispatch[si] - mi[si])/2 + w2*(ma[si] - base_dispatch[si])/2

    # Cumulative deviation of generators not straddling the base dispatch
    deviation_non_si = np.abs(initial[~si] - final[~si])*ramp_time/2 + \
                       np.minimum(np.abs(initial[~si]-base_dispatch[~si]), np.abs(final[~si]-base_dispatch[~si]))*ramp_time

    return np.sum(deviation_si) + np.sum(deviation_non_si)
