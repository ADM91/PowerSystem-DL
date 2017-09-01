# Configuration file containing any auxiliary information required
import numpy as np
from oct2py import octave

# Add Matpower to octave path
octave.addpath('/home/alexander/Documents/MATLAB/matpower6.0')

# Set Matpower options
mp_opt = octave.mpoption('verbose', 0, 'out.all', 0)

case14_droop_constants = np.array([3, 4, 6, 2, 5])

# Convergence constants for slack distribution
distribute_slack_constants = {'tolerance': 0.01,
                              'max iteration': 10}
