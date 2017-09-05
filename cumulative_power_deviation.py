import numpy as np


def cumulative_power_deviation(base_case_contingency, test_result_dist, test_result_opf, ramp_time):
    """
    Solves for the sum deviation from base case generator schedule during the ramping
    period prior to reconnection.  Units come out to MW*min.

    :param base_case_contingency: The scheduled generator dispatch
    :param test_result_dist: The initial generator dispatch
    :param test_result_opf: The target generator dispatch
    :param ramp_time: Time taken to ramp all generators (minutes)
    :return: Cumulative energy deviated from the base schedule (MW*minute)
    """

    # Base dispatch
    base = base_case_contingency['gen'][:, 1]

    # Initial dispatch
    initial = test_result_dist['gen'][:, 1]

    # Final dispatch
    final = test_result_opf['gen'][:, 1]

    # Calculate sum of dispatch deviation
    # need to find if the base straddles the initial and final states
    mi = np.minimum(initial, final)
    ma = np.maximum(initial, final)
    si = np.logical_and(base > mi, base < ma)  # straddle index array (si)

    # Length (min) of triangles straddling the base
    w1 = ramp_time/(1 + np.abs(base[si]-ma[si])/np.abs(base[si]-mi[si]))
    w2 = ramp_time - w1

    # Cumulative deviation of the generators straddling the base dispatch
    deviation_si = w1*(base[si] - mi[si])/2 + w2*(ma[si] - base[si])/2

    # Cumulative deviation of generators not straddling the base dispatch
    deviation_non_si = np.abs(initial[~si] - final[~si])*ramp_time/2 + \
                       np.minimum(np.abs(initial[~si]-base[~si]), np.abs(final[~si]-base[~si]))*ramp_time

    return np.sum(deviation_si) + np.sum(deviation_non_si)
