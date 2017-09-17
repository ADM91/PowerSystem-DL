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

# Constants for the 5 generators in case 14
case14_droop_constants = np.array([3, 4, 6, 2, 5])  # in percent
case14_ramp_rates = np.array([25, 15, 15, 20, 30])  # MW/min

# Convergence constants for slack distribution
distribute_slack_constants = {'tolerance': 0.01,
                              'max iteration': 10}

# Line ratings for case 14
line_ratings = np.array([158.2042239,  75.60872119,   73.32406193,   56.15290218,
                        41.5327262,    23.71143451,    63.1721204,   29.69650462,
                        16.08544234,   45.81713343,    8.16992351,    8.17862595,
                        19.15906164,   17.16297051,   28.66273919,    6.71776961,
                        10.09399843,    4.11547005,    1.78165164,    5.90810207])

line_ratings = line_ratings + 50

# Modes: 'debug'
mode = 'debug'
