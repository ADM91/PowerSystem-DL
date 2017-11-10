from oct2py import octave
import numpy as np


def cumulative_losses(state_1, state_2, ramp_time, ideal_losses):
    """
    Cumulative losses during generator ramping are calculated. Units in MW*min.

    :param state_1: Solved Matpower case with initial generation schedule
    :param state_2: Solved Matpower case with final generation schedule
    :param ramp_time: Total time (minutes) of ramp action
    :return:
    """

    # Calculate losses before and after ramp
    initial = state_1['losses']
    final = state_2['losses']

    # Cumulative real energy losses during ramp (MW*min)
    losses = (np.abs(initial - final)/2 + np.min([initial, final]))*ramp_time

    # Return the deviation from ideal case losses (negative indicates loss savings)
    return -(ideal_losses - losses)
