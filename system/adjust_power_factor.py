import numpy as np


def adjust_power_factor(octave, gen_matrix):

    # identify dispatchable loads in the gen matrix
    load_ind = np.where(octave.isload(gen_matrix) == 1)[0]

    # Calculate the expected power factor
    p_g = gen_matrix[load_ind, 1]
    q_max = gen_matrix[load_ind, 3]
    q_min = gen_matrix[load_ind, 4]
    p_max = gen_matrix[load_ind, 8]
    p_min = gen_matrix[load_ind, 9]
    expected_pf = np.divide(p_max - p_min, q_max - q_min)

    # Adjust q_g to match the expected power factor
    gen_matrix[load_ind, 2] = np.divide(p_g, expected_pf)

    return gen_matrix
