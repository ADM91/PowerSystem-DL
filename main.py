from itertools import permutations

import numpy as np
from matplotlib import pyplot as plt
from oct2py import octave

from auxiliary.SPA_difference import SPA_difference
from auxiliary.config import mp_opt, \
    case14_ramp_rates, \
    line_ratings
from auxiliary.visualize_network import visualize_network
from cost.objective_function import objective_function
from set_opf_constraints import set_opf_constraints
from system.branch_deactivate import branch_deactivate
from system.check_extract_islands import check_extract_islands


# Test code
# -----------------

# TODO: Add unserved load to the objective function
# TODO: Transform objective to a monetary equivalent with one output.
# TODO: Implement the ghost line method to simulate energizing one end of a disonnected line
# TODO: Implement more error handling, what if something doesnt converge?


# TODO: if there is opf convergence failure, set island to blackout
# TODO: to study effect of changing load shedding cost use matpower function modcost
# TODO: if there are islands without loads or gen, treat all elements within island as deactivated (add to list)


# ---------NOTES------------
# If an blackout island is connected to functioning island, I have problems.  Opf doesn't converge (at least
# last time i tried).  Also, generators that were cut off (not a part of any island) do not appear back in the
# generator matrix, and seems to be lost.  I have to come up with a method to retain the generators and loads
# lost between islands...  Maybe visualizing what belongs to what island is my next move.

# A dispatchable load that is lost between islands is not recovered when that bus is recovered by the system.
# these loads are defined as generators, so the same must be true for generators.  I need a way of tracking the
# "left over" generators and loads. -- Next on the list

# There must be some mistake in the code that detects if line is outside
# an island.  Last test showed that lines that don't show up in the branch
# data matrix are a part of the current island.


# ---------Test code------------

from pprint import PrettyPrinter
import numpy as np
from system.PowerSystem import PowerSystem
from oct2py import octave
from auxiliary.config import mp_opt, \
    case14_ramp_rates, \
    line_ratings,\
    dispatchable_loads


pp = PrettyPrinter(indent=4)

base_case = octave.loadcase('case14')
base_case['branch'][:, 5] = line_ratings  # Have to add line ratings
base_result = octave.runpf(base_case, mp_opt)

ps = PowerSystem(base_result, n_deactivated=8)
pp.pprint(ps.islands.keys())
pp.pprint(ps.islands['blackout'])

# Nans in (real inj = branches), (real gen = gen), (fixed load = bus)
pp.pprint(ps.evaluate_state(list(ps.islands.values())))


ps.visualize_state()

for i, island in enumerate(ps.islands):
    print('island %s: load %s' % (i, island['is_load']))
    print('island %s: gen %s' % (i, island['is_gen']))


dis_el = ps.disconnected_elements

ps.current_state['losses']

# Reconnect a line
# ps.action_line(dis_el['lines'][0])

from matplotlib import pyplot as plt
plt.ion()
count = 1
for line in dis_el['lines']:

    print(dis_el)
    ps.action_line(line)

    # Evaluate islands
    ps.evaluate_islands()

    # Get system state
    ps.current_state = ps.evaluate_state(ps.islands_evaluated)

    ps.current_state['losses']

    # Plot the state
    ps.visualize_state(fig_num=count)

    count += 1

    input("Press Enter to continue...")

# -----------------




# Open up IEEE 14 bus test case and run pf
# base_case = octave.loadcase('case14')
# base_case['branch'][:, 5] = line_ratings  # Have to add line ratings
# base_result = octave.runpf(base_case, mp_opt)
#
#
# # Visualize the graph
# visualize_network(base_result)
#
# # Remove random line(s) and run pf
# base_case_contingency, branch_deactivated = branch_deactivate(case=base_case, n_branches=8)
#
#
# islands = check_extract_islands(base_case_contingency)
# islands.shape
#
# # Get an idea for the situation
# for i, island in enumerate(islands):
#     print('island %s: load %s' % (i, island['is_load']))
#     print('island %s: gen %s' % (i, island['is_gen']))
#
#
# # Make copy of islands to manipulate for opf
# from copy import deepcopy
# islands_opf = deepcopy(islands)
#
# # For islands with gen and load, set up opf
# for i, isl in enumerate(islands_opf):
#
#     # Run opf if island has both gen and load
#     if isl['is_gen'] and isl['is_load']:
#         print('here')
#         isl = set_opf_constraints(isl, set_gen=True, set_loads=True)
#
#     # Run opf on islands
#     opf_result = octave.runopf(isl, mp_opt)
#
#     # Do some error handling if it doesn't converge
#
# # Evaluate the total system state. (load state, gen state, line injection state)
#
#
#     # SPA differences at each branch of base and test cases
#     if result_distr:
#         base_diffs = SPA_difference(base_result)
#         test_diffs = SPA_difference(result_distr)
#         # print(base_diffs[:, 1] - test_diffs[:, 1])
#         print('SPA of lines prior to deactivation: %s' % base_diffs[branch_deactivated, 1])
#         print('SPA of lines after deactivation: %s' % test_diffs[branch_deactivated, 1])
#     else:
#         print('Could not calculate SPA differences')
#
#
# # Generate a list of all permutations of restoration order
# perm = list(permutations(branch_deactivated))
# # Preallocate outputs of objective function
# objective_store = np.zeros((len(perm), 3))
#
# for i, p in enumerate(perm):
#     objective_store[i, :] = objective_function(base_case_contingency=base_case_contingency,
#                                                result=result_distr,
#                                                ramp_rates=case14_ramp_rates,
#                                                order=p,
#                                                slack_ind=slack_ind,
#                                                max_SPA=20)
#
# # Plot the results
# plt.subplot(311)
# plt.plot(objective_store[:, 0], 'ro-')
# plt.title('restoration time')
# plt.subplot(312)
# plt.plot(objective_store[:, 1], 'bo-')
# plt.title('total energy deviation')
# plt.subplot(313)
# plt.plot(objective_store[:, 2], 'go-')
# plt.title('total losses')
# plt.xlabel('Solution number')