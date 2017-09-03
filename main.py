# import matplotlib.pyplot as plt
import numpy as np
from oct2py import octave
from branch_deactivate import branch_deactivate
from SPA_difference import SPA_difference
from distribute_slack import distribute_slack
from set_opf_constraints import set_opf_constraints
from config import case14_droop_constants, distribute_slack_constants, mp_opt


# Open up IEEE 14 bus test case and run pf
base_case = octave.loadcase('case14')
base_result = octave.runpf(base_case, mp_opt)

# Remove random line(s) and run pf
test_case, branch_deactivated = branch_deactivate(case=base_case, n_branches=3)

# TODO: write method to check which lines are deactived... might be useful

# Distribute slack using LFC (droop constants)
test_result_dist = distribute_slack(test_case=test_case,
                                    slack_ind=np.nonzero(test_case['bus'][:, 1] == 3),
                                    droop_constants=case14_droop_constants,
                                    converge_options=distribute_slack_constants,
                                    mp_options=mp_opt)

# SPA differences at each branch of base and test cases
if test_result_dist:
    base_diffs = SPA_difference(base_result)
    test_diffs = SPA_difference(test_result_dist)
    # print(base_diffs[:, 1] - test_diffs[:, 1])
    print('SPA of lines prior to deactivation: %s' % base_diffs[branch_deactivated, 1])
    print('SPA of lines after deactivation: %s' % test_diffs[branch_deactivated, 1])

else:
    print('Could not calculate SPA differences')

# Set up OPF!
test_case_opf = set_opf_constraints(test_case, branch_deactivated, max_SPA=10)

# Run OPF
test_result_opf = octave.runopf(test_case_opf, mp_opt)

# Did it work??
test_opf_diffs = SPA_difference(test_result_opf)
print('SPA of deactivated lines: %s' % test_opf_diffs[branch_deactivated, 1])
print('Original active: %s \n OPF active: %s \n\n Original reactive: %s \n OPF reactive: %s'
      % (test_case['gen'][:, 1],
         test_result_opf['gen'][:, 1],
         test_case['gen'][:, 2],
         test_result_opf['gen'][:, 2]))
