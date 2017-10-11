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

# TODO: I am getting errors because some dispatch load is being overlooked (shows up as nan)

# TODO: Set generator status to 0 if it is in blackout area

# TODO: Add status information to the current state


# ---------Other notes------------
# If an blackout island is connected to functioning island, I have problems.  Opf doesn't converge (at least
# last time i tried).  Also, generators that were cut off (not a part of any island) do not appear back in the
# generator matrix, and seems to be lost.  I have to come up with a method to retain the generators and loads
# lost between islands...  Maybe visualizing what belongs to what island is my next move.

# A dispatchable load that is lost between islands is not recovered when that bus is recovered by the system.
# these loads are defined as generators, so the same must be true for generators.  I need a way of tracking the
# "left over" generators and loads. -- Next on the list

# There must be some mistake in the code that detects if line is outside
# an island.  Last test showed that lines that don't show up in the branch
# data matrix are a part of the current island. -- Fixing now


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
    dispatchable_loads


pp = PrettyPrinter(indent=4)
np.set_printoptions(precision=2)

base_case = octave.loadcase('case14')
base_case['branch'][:, 5] = line_ratings  # Have to add line ratings
base_result = octave.runpf(base_case, mp_opt)

ps = PowerSystem(base_result, n_deactivated=12, verbose=1, verbose_state=0)
ps.action_list
# Why are these not the same???
ps.islands['0']['branch'][:,13]
ps.islands_evaluated['0']['branch'][:, 13]
ps.islands.keys()


out = ps.action_line(ps.action_list['lines'][0])
pp.pprint(ps.blackout_connections)

anim = visualize_state(ps.ideal_case, ps.ideal_state, out)

ps.visualize_state(out)

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
