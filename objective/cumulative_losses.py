from oct2py import octave
import numpy as np


def cumulative_losses(state_1, state_2, time, ideal_losses):
    """
    Cumulative losses during generator ramping are calculated. Units in MW*min.

    :param state_1: Solved Matpower case with initial generation schedule
    :param state_2: Solved Matpower case with final generation schedule
    :param time: Total time (minutes) of ramp action
    :return:
    """

    # Calculate losses before and after ramp
    initial = state_1['losses']
    final = state_2['losses']

    # Cumulative real energy losses during ramp (MW*min)
    avg_loss = np.mean([initial, final])

    # print('losses: %.1f, %.1f, %.1f' % (initial, final, avg_loss))

    # Return the deviation from ideal case losses (negative indicates loss savings)
    return -(ideal_losses - avg_loss)*time
