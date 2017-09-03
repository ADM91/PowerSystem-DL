# Configuration file containing any auxiliary information required
import numpy as np
from oct2py import octave

# Add Matpower to octave path
octave.addpath('/home/alexander/Documents/MATLAB/matpower6.0')

# Set Matpower options
mp_opt = octave.mpoption('verbose', 1,
                         'out.sys_sum', 0,
                         'out.gen', 1,
                         'out.lim.all', 1,
                         'opf.ac.solver', 'MIPS',
                         'opf.ignore_angle_lim', 0)

# Droop constants for the 5 generators in case 14
case14_droop_constants = np.array([3, 4, 6, 2, 5])

# Convergence constants for slack distribution
distribute_slack_constants = {'tolerance': 0.01,
                              'max iteration': 10}
