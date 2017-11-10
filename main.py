# -------- To do list---------

# TODO: Add unserved load to the objective function
# TODO: Transform objective to a monetary equivalent with one output.
# TODO: Implement the ghost line method to simulate energizing one end of a disonnected line
# TODO: Implement more error handling, what if something doesnt converge?

# TODO: if there is opf convergence failure, set island to blackout... maybe
# TODO: to study effect of changing load shedding cost use matpower function modcost

# TODO: Set generator status to 0 if it is in blackout area

# ---------Old/Fixed Concerns------------

# If a blackout island is connected to functioning island, I have problems.  Opf doesn't converge (at least
# last time i tried).  Also, generators that were cut off (not a part of any island) do not appear back in the
# generator matrix, and seems to be lost.  I have to come up with a method to retain the generators and loads
# lost between islands...  Maybe visualizing what belongs to what island is my next move.
# -Fixed-

# There must be some mistake in the code that detects if line is outside
# an island.  Last test showed that lines that don't show up in the branch
# data matrix are a part of the current island.
# -Fixed-

# When a fixed load is associated with a bus, the load is automatically attached when the bus
# is re-introduced to the network.  I want to save this action as another action...
# -Fixed-

# A dispatchable load that is lost between islands is not recovered when that bus is recovered by the system.
# these loads are defined as generators, so the same must be true for generators.  I need a way of tracking the
# "left over" generators and loads. -- Next on the list
# -Fixed-

# The solution to the load problems is creating a load tracking variable that is acted upon in the
# load action function.  The function basically will remove the load from the action list, if the load
# is in a blackout area, have it immediately enacted when the bus is re-energized.  This might be
# a bit messy code-wise, but will have to due for now.
# -Fixed-

# ---------Current Concerns------------

# If conditions are too extreme (Too many lines removed etc.) I get crazy spa diffs
# and the spa constraint is not effective in reducing them.  There must be some
# convergence issues that are not detected.

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

# Should I give dispatchable loads ramp rates and evaluate their ramp time for the
# objective function? Currently its assumed that they change instantaneously.

# ---------Testing------------

from pprint import PrettyPrinter
import numpy as np
from oct2py import octave
from auxiliary.config import mp_opt, \
    line_ratings, \
    deconstruct_1, deconstruct_2, deconstruct_3, deconstruct_4, deconstruct_5, deconstruct_6
from auxiliary.visualize_state import visualize_state
from system.PowerSystem import PowerSystem
from cost.objective_function import objective_function


pp = PrettyPrinter(indent=4)
np.set_printoptions(precision=2)

base_case = octave.loadcase('case14')
base_case['branch'][:, 5] = line_ratings  # Have to add line ratings
base_result = octave.runpf(base_case, mp_opt)

# Instantiate the PowerSystem class
ps = PowerSystem(base_result, deactivated=deconstruct_5, verbose=0, verbose_state=0)

# Perform all required restoration actions on network
states = []
# states.append(ps.action_line([7, 8])[0])    # Blackout network
# states.append(ps.action_line([10, 11])[0])  # Blackout network
while len(ps.action_list['line']) > 0:
    for state in ps.action_line(ps.action_list['line'][0]):
        states.append(state)
while len(ps.action_list['fixed load']) > 0:
    for state in ps.action_fixed_load(ps.action_list['fixed load'][0]):
        states.append(state)
while len(ps.action_list['gen']) > 0:
    for state in ps.action_gen(ps.action_list['gen'][0]):
        states.append(state)
while len(ps.action_list['dispatch load']) > 0:
    for state in ps.action_dispatch_load(ps.action_list['dispatch load'][0]):
        states.append(state)

pp.pprint(ps.blackout_connections)
anim = visualize_state(ps.ideal_case, ps.ideal_state, states, frames=10, save=False)


[time, energy, cost] = objective_function(states[0:2], ps.ideal_state)
