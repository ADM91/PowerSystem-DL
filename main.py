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


# -------- To do list---------

# TODO: Add unserved load to the objective function
# TODO: Transform objective to a monetary equivalent with one output.
# TODO: Implement the ghost line method to simulate energizing one end of a disonnected line
# TODO: Implement more error handling, what if something doesnt converge?

# TODO: if there is opf convergence failure, set island to blackout... maybe
# TODO: to study effect of changing load shedding cost use matpower function modcost

# TODO: Set generator status to 0 if it is in blackout area

# ---------Old Concerns------------

# If a blackout island is connected to functioning island, I have problems.  Opf doesn't converge (at least
# last time i tried).  Also, generators that were cut off (not a part of any island) do not appear back in the
# generator matrix, and seems to be lost.  I have to come up with a method to retain the generators and loads
# lost between islands...  Maybe visualizing what belongs to what island is my next move.
# -Fixed-

# There must be some mistake in the code that detects if line is outside
# an island.  Last test showed that lines that don't show up in the branch
# data matrix are a part of the current island.
# -Fixed-


# ---------Current Concerns------------

# If conditions are too extreme (Too many lines removed etc.) I get crazy spa diffs
# and the spa constraint is not effective in reducing them.  There must be some
# convergence issues that are not detected.

# When a fixed load is associated with a bus, the load is automatically attached when the bus
# is re-introduced to the network.  I want to save this action as another action...

# A dispatchable load that is lost between islands is not recovered when that bus is recovered by the system.
# these loads are defined as generators, so the same must be true for generators.  I need a way of tracking the
# "left over" generators and loads. -- Next on the list

# The solution to the load problems is creating a load tracking variable that is acted upon in the
# load action function.  The function basically will remove the load from the action list, if the load
# is in a blackout area, have it immediately enacted when the bus is re-energized.  This might be
# a bit messy code-wise, but will have to due for now.

# Re-solving for a steady state after line reconnection might not be the
# right way to approach the problem.  I might be just moving back to a less
# condusive state for the next line reconnection.  The opimization might
# therefore not reach a realistic conclusion. Be thinking about how
# to circumvent this problem... the solution might result in the need for
# action parallelization.  Need to read some papers on that first.
# Possible solution is putting the generator setpoints in the
# hands of the optimizer, but I think this vastly complicates the optimization.

# When connecting a blackout bus to an energized system, remember that a blackout
# bus may have more than one line connecting to the energized system, I get an error
# when the second line to the blackout bus is connected.  (I thought that the
# bus would no longer be in a blackout area after the first line is connected...
# Im not sure what is going on.)

# ---------Testing code------------

from pprint import PrettyPrinter
from matplotlib import pyplot as plt
from matplotlib import animation
import numpy as np
from oct2py import octave
import numpy as np
from system.PowerSystem import PowerSystem
from oct2py import octave
from visualize_state import visualize_state
from auxiliary.config import mp_opt, \
    case14_ramp_rates, \
    line_ratings,\
    dispatchable_loads,\
    deconstruct_1, deconstruct_2, deconstruct_3


pp = PrettyPrinter(indent=4)
np.set_printoptions(precision=2)

base_case = octave.loadcase('case14')
base_case['branch'][:, 5] = line_ratings  # Have to add line ratings
base_result = octave.runpf(base_case, mp_opt)

ps = PowerSystem(base_result, deactivated=deconstruct_3, verbose=1, verbose_state=0)
ps.action_list
# Why are these not the same???
ps.islands['0']['branch'][:,13]
ps.islands_evaluated['0']['branch'][:, 13]
ps.islands.keys()

states = []
while len(ps.action_list['lines']) > 0:
    for state in ps.action_line(ps.action_list['lines'][0]):
        states.append(state)

# out = ps.action_line([ 7.  ,    8. ]) # Within blkout
# out = ps.action_line([ 4.  ,    7. ])

pp.pprint(ps.blackout_connections)
anim = visualize_state(ps.ideal_case, ps.ideal_state, states)

ps.visualize_state(states)

pp.pprint(ps.current_state)


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
