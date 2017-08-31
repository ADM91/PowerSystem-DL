# import pypower.api as pp
# import matplotlib.pyplot as plt
# import numpy as np
from oct2py import octave
from branch_remove import branch_remove
from SPA_difference import SPA_difference

# Add MATPOWER to octave path
octave.addpath('/home/alexander/Documents/MATLAB/matpower6.0')

# Open up IEEE 14 bus test case and run pf
case = octave.loadcase('case14')
base_result = octave.runpf(case)

# Remove a random line and run pf
test_case, branch_removed = branch_remove(case, 5)
test_result = octave.runpf(test_case)

# Distribute slack using LFC (droop constants)



# SPA differences at each branch of base and test cases
base_diffs = SPA_difference(base_result)
test_diffs = SPA_difference(test_result)

print(base_diffs - test_diffs)




