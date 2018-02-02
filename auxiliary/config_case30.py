# Configuration file containing any auxiliary information required
import numpy as np
from oct2py import octave


# Add Matpower to octave path
octave.addpath('/home/alexander/Documents/MATLAB/matpower6.0')
octave.addpath('/home/alexander/Documents/MATLAB/matpower6.0/@opf_model')
octave.addpath('/home/alexander/Documents/MATLAB/opf_solvers/minopf5.1_linux')
octave.addpath('/home/alexander/Documents/MATLAB/opf_solvers/tspopf5.1_linux64')

# Set Matpower options
mp_opt = octave.mpoption('verbose', 0,
                         'out.all', 0,
                         'out.sys_sum', 0,
                         'out.gen', 0,
                         'out.lim.all', 0,
                         'opf.ac.solver', 'MIPS',
                         'opf.ignore_angle_lim', 0,
                         'opf.init_from_mpc', 1)

# Constants for the 6 generators in case 30
droop_constants = np.array([3, 3, 3, 3, 3, 3])  # in percent
ramp_rates = np.array([10, 10, 10, 10, 10, 10])  # MW/min

# Convergence constants for slack distribution
distribute_slack_constants = {'tolerance': 0.01,
                              'max iteration': 10}

# Line ratings for case 30 already exist

# Ones indicate buses w/ dispatchable loads
# dispatchable_loads = np.array([0, 1, 0, 0, 0,
#                                0, 0, 1, 0, 0,
#                                0, 0, 0, 0, 0,
#                                0, 0, 0, 0, 0,
#                                1, 0, 0, 0, 0,
#                                0, 0, 0, 0, 1])

dispatchable_loads = np.array([0, 1, 0, 0, 0,
                               0, 1, 1, 0, 0,
                               0, 0, 0, 0, 0,
                               0, 0, 0, 0, 0,
                               0, 0, 0, 0, 0,
                               0, 0, 0, 0, 0])



# Load objective ($/MWh)
dispatch_load_cost = np.array([1, 1, 1]).reshape((-1, 1))
fixed_load_cost = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]).reshape((-1, 1))
loss_cost = 1
disp_dev_cost = 0.1

# Deconstructed cases
# ---------------Deconstruction 1-----------------
deconstruct_1 = np.array([False, False, False, False, False, False, False, False, False, False,
                          False, False, False, False, True, True, True, True, True, True,
                          False, True, False, False, False, False, False, False, False, True,
                          False, False, False, False, False, False, False, False, False, False,
                          False])


deconstruct_2 = np.array([False, False, False, False, False, False, False, False, False, False,
                          False, False, False, False, True, True, True, True, True, True,
                          False, True, False, False, False, False, False, False, False, True,
                          False, True, False, False, False, False, False, False, False, False,
                          False])

# ---------------Deconstruction 2-----------------
# # Connects two non-energized buses
# deconstruct_2 = np.array([True, False, False, True,
#                           False, False, True, True,
#                           False, True, False, True,
#                           False, False, False, True,
#                           False, True, True, False])
#
# # ---------------Deconstruction 3-----------------
# # Connects a blackout bus with two lines to the energized system
# deconstruct_3 = np.array([False, False, True, True,
#                           True, False, False, True,
#                           False, True, True, True,
#                           False, True, False, False,
#                           False, True, False, False])
#
# # ---------------Deconstruction 4-----------------
# # Connects a blackout network
# deconstruct_4 = np.array([False, False, True, False,
#                           False, False, False, True,
#                           False, True, True, True,
#                           True, True, True, True,
#                           False, True, True, False])
#
# # ---------------Deconstruction 5-----------------
# # Disables fixed loads
# deconstruct_5 = np.array([True, False, True, True,
#                           True, False, False, False,
#                           False, True, True, True,
#                           False, False, False, False,
#                           False, True, True, False])
#
# # ---------------Deconstruction 6-----------------
# # Disables generators
# deconstruct_6 = np.array([True, False, True, True,
#                           True, True, False, False,
#                           False, False, False, False,
#                           False, False, False, False,
#                           False, False, False, False])
#
#
# # ---------------Deconstruction 7-----------------
# # have doable action list
# deconstruct_7 = np.array([False, False, False, True,
#                           False, False, True, False,
#                           False, False, False, True,
#                           False, False, False, False,
#                           False, True, False, False])

# Lines:
# array([[  1.,   2.],
#        [  1.,   3.],
#        [  2.,   4.],
#        [  3.,   4.],
#        [  2.,   5.],
#        [  2.,   6.],
#        [  4.,   6.],
#        [  5.,   7.],
#        [  6.,   7.],
#        [  6.,   8.],
#        [  6.,   9.],
#        [  6.,  10.],
#        [  9.,  11.],
#        [  9.,  10.],
#        [  4.,  12.],
#        [ 12.,  13.],
#        [ 12.,  14.],
#        [ 12.,  15.],
#        [ 12.,  16.],
#        [ 14.,  15.],
#        [ 16.,  17.],
#        [ 15.,  18.],
#        [ 18.,  19.],
#        [ 19.,  20.],
#        [ 10.,  20.],
#        [ 10.,  17.],
#        [ 10.,  21.],
#        [ 10.,  22.],
#        [ 21.,  22.],
#        [ 15.,  23.],
#        [ 22.,  24.],
#        [ 23.,  24.],
#        [ 24.,  25.],
#        [ 25.,  26.],
#        [ 25.,  27.],
#        [ 28.,  27.],
#        [ 27.,  29.],
#        [ 27.,  30.],
#        [ 29.,  30.],
#        [  8.,  28.],
#        [  6.,  28.]])

