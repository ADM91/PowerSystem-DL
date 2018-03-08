import numpy as np
from glob import glob


def pick_random_state(octave):

    files = glob('/home/alexander/Documents/MATLAB/MPCfiles/*')
    n_files = len(files)

    # while True:

    i = np.random.choice(n_files)
    base_case = octave.loadcase(files[i])

    # Switch all lines on
    base_case['branch'][:, 10] = 1

    return base_case, files[i]
