from oct2py import octave
import numpy as np


def cumulative_losses(before, after, ramp_time):
    """
    Cumulative losses during generator ramping are calculated. Units in MW*min.

    :param before: Solved Matpower case with initial generation schedule
    :param after: Solved Matpower case with final generation schedule
    :param ramp_time: Total time (minutes) of ramp action
    :return:
    """

    # Calculate losses before and after ramp
    initial = np.real(np.sum(octave.get_losses(before['baseMVA'], before['bus'], before['branch'])))
    final = np.real(np.sum(octave.get_losses(after['baseMVA'], after['bus'], after['branch'])))

    # Cumulative real energy losses during ramp (MW*min)
    losses = (np.abs(initial - final)/2 + np.min([initial, final]))*ramp_time

    return losses
