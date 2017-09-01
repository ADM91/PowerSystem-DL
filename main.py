# import matplotlib.pyplot as plt
import numpy as np
from oct2py import octave
from branch_deactivate import branch_deactivate
from SPA_difference import SPA_difference
from distribute_slack import distribute_slack
from config import case14_droop_constants, distribute_slack_constants, mp_opt


# Open up IEEE 14 bus test case and run pf
base_case = octave.loadcase('case14')
base_result = octave.runpf(base_case, mp_opt)

# Remove random line(s) and run pf
test_case, branch_deactivated = branch_deactivate(case=base_case, n_branches=3)
test_result = octave.runpf(test_case, mp_opt)

# Slack bus index
slack_ind = np.nonzero(test_case['bus'][:, 1] == 3)

# Distribute slack using LFC (droop constants)
test_result_dist = distribute_slack(test_case=test_case,
                                    base_slack=base_result['gen'][slack_ind, 1],
                                    droop_constants=case14_droop_constants,
                                    converge_options=distribute_slack_constants,
                                    mp_options=mp_opt)

# SPA differences at each branch of base and test cases
if test_result_dist:
    base_diffs = SPA_difference(base_result)
    test_diffs = SPA_difference(test_result_dist)
    print(base_diffs[:, 1] - test_diffs[:, 1])

else:
    print('Could not calculate SPA differences')




