# -------- To do list---------

# TODO: Implement the ghost line method to simulate energizing one end of a disonnected line
# TODO: Implement more error handling, what if something doesnt converge?
# TODO: if there is opf convergence failure, set island to blackout... maybe (only at initial degraded state)
# TODO: study effect of changing load shedding objective use matpower: function modcost
# TODO: Implement genetic optimization
# TODO: still have issue with connecting between blackout and energized buses... dammmmn
# TODO: Build a sequence tester, and visualizer (will help validate the optimizations)
# TODO: Create a consistent data format returned by each optimizer - so that I can use a function to compare results
# TODO: Improve vis function to do comprehensive visualization of optimization results.
# TODO: Move testing to IEEE 30 bus network, its more realistic but still small enough to not take too much computing
# TODO: update the random search algorithm to work with the action map dictionary instead of sequence decoder function


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

# When connecting a blackout bus to an energized system, remember that a blackout
# bus may have more than one line connecting to the energized system, I get an error
# when the second line to the blackout bus is connected.  (I thought that the
# bus would no longer be in a blackout area after the first line is connected...
# Im not sure what is going on.)
# -Fixed- Simple bug, needed to move the bus the the energized island

# Need to implement fail-safes to prevent enabling a load or generator within a
# blackout area... for restorations that violate rules, implement a function to
# delay the violating action and rerun (feasibility preserving function)
# - Implemented the feasibility preserver for random search, but need a
# more robust violation detector because its impractical to connect blackout lines
# -Fixed- Im just returning an empty state list if this occurs, the optimizers know that this means the action
# is invalid

# Tree search optimization will generate the tree whilst optimizing.
# Can therefore view what paths have been explored after optimization.
# If tree is generated prior to optimization, it will be too large to keep in memory if number of actions is
# greater than 9 or 10. Maybe 11 if pruning is performed during tree generation.  To prune, the tree has
# to have information about what the network looks like and this adds substantial computation cost.
# -Fixed- I just generate the tree as optimization requires.

# Where snapshots are taken during restoration actions:

# LINES - within island
# Before gen reschedule
# After gen reschedule & Before connection
# After connection

# LINES - between energized and blackout
# Before connection
# After connection

# LINES - between islands
# Before connection
# After connection

# FIXED LOADS
# before connection
# after connection (the load parameters are taken from ideal case)

# DISPATCHABLE LOADS
# before connection
# after connection (the load is enabled in the gen matrix, remember these are modeled as generators)

# GENERATORS
# before connection
# after connection (the generator is enabled in the gen matrix)

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
# This is important to touch on in the thesis if I don't get around to addressing this.
# I should at least try to do a study to see the effect of this 'problem'.

# Should I give dispatchable loads ramp rates and evaluate their ramp time for the
# objective function? Currently its assumed that they change instantaneously.
# - Probably a good idea to implement this.

# Restoration takes about 5 seconds on 14 bus system... this is too slow.
# Look at using a more efficient opf. Maybe benchmark them and include in thesis.

# So why is the cost wayy different in the random search optimization and the tree search?
# Lets take a look at the objective function:
# Input: a list of states and ideal state for reference
# Takes two consecutive states and finds generation difference
# Calculates ramp time between these states
# Calculates energy not served, generator deviation, loss difference over this time period
# Calculates cost of energy values
# Iterates for every consecutive pair of states in state list and saves data
# Calculates cumulative cost
# May have been fixed already, but would like to verify with a sequence tester... this is next on the list

# I think with the 14 bus network, the lowest hanging fruit is always the best option, therefore the tree search is
# great.  This might not be true on larger networks (the best option may be to create a route directly to a lost load).
# I can test these ideas by designing a degraded state on larger networks.

# What results do I want to show from these optimizations???
# - Compare variables to total restoration cost (to help understand general good practices):
#   - restoration time
#   - lost load
#   - losses
# WIP

# Currently, I have an issue when connecting energized island to blackout bus... a duplicate bus gets generated in the
# island bus matrix.  The voltage angle and magnitude differ, and one has lagrange multipliers. This means that when
# I run the island evaluation, it fails.
# This must be caused by a bookkeeping error.  I need to look diligently through the line connection code.

# Do I really need islands_evaluated? Can't I just maintain islands with matpower opf result with additional info?


# ---------Testing------------

import numpy as np
from anytree import RenderTree
from oct2py import octave

from auxiliary.config import mp_opt, \
    line_ratings, \
    deconstruct_7
from optimize.RestorationTree import RestorationTree
from optimize.execute_sequence import execute_sequence
from optimize.random_search import random_search_opt
from optimize.sequence_decoder import decode_sequence
from optimize.stochastic_tree_search import stochastic_tree_search
from system.PowerSystem import PowerSystem
from test.test_sequence import test_sequence
from visualize.visualize_cost_opt import visualize_cost_opt
from visualize.visualize_state import visualize_state
from test.test_revert import test_revert
from optimize.action_map import create_action_map

np.set_printoptions(precision=2)

# Evaluate base case power system
base_case = octave.loadcase('case14')
base_case['branch'][:, 5] = line_ratings  # Have to add line ratings
base_result = octave.runpf(base_case, mp_opt)

# Instantiate PowerSystem class
ps = PowerSystem(base_result,
                 spad_lim=10,
                 deactivated=deconstruct_7,
                 verbose=0,
                 verbose_state=0)

action_map = create_action_map(ps.action_list)
ps.reset()
# First action
ps.action_line([2, 4])
ps.action_line([4, 5])
[state_store, time_store, energy_store, cost_store], l1 = test_revert(ps, [3,3,3,3,3,3,3,3,3], action_map)

# Checking if original state stays the same throughout the test
# ----------------------------------------------------------------
from matplotlib import pyplot as plt
from objective.objective_function import objective_function
[time, energy, cost] = objective_function(l1, ps.ideal_state)  # Everything is zero because time between states is zero
plt.plot(energy['dispatch deviation'])
# ----------------------------------------------------------------
# Looks like it does! That means the information is not translated correctly to the ps model using ps.revert

# Need to investigate if the revert inconsistency occurs if I revert back not to the ideal case - it does
# Need to look at the actual states and figure out where the inconsistencies are - then look for how that might happen

# Detect differences between states (real injection)
len(state_store)
state_store[0]  # inital
state_store[1]  # Prelim state (should be same as initial)
state_store[0]['real inj'] - state_store[1]['real inj']  # Good these are the same

state_store[2]  # Reschedule for connection
state_store[3]  # State after connection (end)
state_store[2]['real inj'] - state_store[3]['real inj']


state_store[4]  # Back to reference state
state_store[3]['real inj'] - state_store[4]['real inj']

state_store[0]['real inj'] - state_store[4]['real inj']  # Good, reference state is the same

state_store[6]  # Reschedule for connection
state_store[7]  # State after connection (end)
(state_store[6]['real inj'] - state_store[7]['real inj']) - (state_store[2]['real inj'] - state_store[3]['real inj'])  # Good change remains the same
(state_store[10]['real inj'] - state_store[11]['real inj']) - (state_store[2]['real inj'] - state_store[3]['real inj'])  # NOT GOOD, the change is different

# Check rescedule for connection
state_store[5]['real inj'] - state_store[9]['real inj']  # Good, have same prelim state before gen redispatch

# Check redispatch state
state_store[6]['real inj'] - state_store[10]['real inj']  # Bad, redispatch states differ...


# Need to look at how the evaluated islands change, might shed some light on the problem, check out ps code to check
# for other dependencies
len(l1)
l1[0]['0']['bus']  # inital
l1[1]['0']['bus']   # Prelim state (should be same as initial)
l1[0]['0']['bus'] - l1[1]['0']['bus']   # Good these are the same

l1[2]['0']['bus']  # Reschedule for connection
l1[3]['0']['bus']  # State after connection (end)
l1[2]['0']['bus'] - l1[3]['0']['bus']  # Zeros means these are the same... they shouldn't be
l1[2]['0']['branch'] - l1[3]['0']['branch']  # Zeros means these are the same... they shouldn't be
l1[2]['0']['gen'] - l1[3]['0']['gen']  # Zeros means these are the same... they shouldn't be
l1[2]['0']['gencost'] - l1[3]['0']['gencost']  # Zeros means these are the same... they shouldn't be


l1[6]['0']['bus']  # Reschedule for connection
l1[7]['0']['bus']  # State after connection (end)
l1[6]['0']['bus'] - l1[7]['0']['bus']  # Zeros means these are the same... they shouldn't be
l1[2]['0']['branch'] - l1[3]['0']['branch']  # Zeros means these are the same... they shouldn't be
l1[2]['0']['gen'] - l1[3]['0']['gen']  # Zeros means these are the same... they shouldn't be
l1[2]['0']['gencost'] - l1[3]['0']['gencost']  # Zeros means these are the same... they shouldn't be

visualize_state(ps.ideal_case, ps.ideal_state, state_store)

plt.plot(cost_store['total'])
plt.plot(cost_store['lost load'])
plt.plot(cost_store['losses'])
plt.plot(cost_store['dispatch deviation'])

plt.plot(energy_store['lost load'])
plt.plot(energy_store['dispatch deviation'])
plt.plot(energy_store['losses'])



# Revealed bug: actions do not always yield same results after reversion.  Its the same after first reversion, but
# Changes after third. What the hell?
# Maybe the ideal state changes?? Shouldn't, don't think it does.
# I get basically the same result for EVERY action! The revert function is deeply flawed, this is important.

# Test stochastic tree search
# -------------------------------------
tree = RestorationTree(ps)
all_data, action_map = stochastic_tree_search(ps,
                                              tree,
                                              opt_iteration=1,
                                              res_iteration=1,
                                              method='cost',
                                              verbose=1,
                                              save_data=0,
                                              folder='Tree-search-cost-d5')

[state_list, time_store, energy_store, cost_store] = test_sequence(ps, [2, 0, 1, 3], action_map)
[state_store, time_store, energy_store, cost_store] = test_revert(ps, [2, 2, 2, 2, 2], action_map)


visualize_state(ps.ideal_case, ps.ideal_state, state_list)


# visualize_cost_opt('Tree-search-cost-d1', title='Tree search: Case 1', fig_num=3)

# -------------------------------------


# Random search optimizer
data = random_search_opt(ps, opt_iteration=1, res_iteration=1, verbose=1, save_data=0, folder='test')




# -------------------------------------

tree = RestorationTree(ps)
tree.action_list
tree.generate_tree()
RenderTree(tree.root)



# Perform single sequence
n_actions = int(np.sum([len(item) for item in ps.action_list.values()]))
sequence = np.random.permutation(n_actions)
action_sequence = decode_sequence(ps.action_list, sequence)
states = execute_sequence(ps, action_sequence)
animation = visualize_state(base_case, ps.ideal_state, states, fig_num=1, frames=5, save=True)


# Perform random search optimization
output = random_search_opt(ps,
                           opt_iteration=30,
                           res_iteration=50,
                           verbose=1,
                           save_data=1,
                           folder='Rand-search-d3')

visualize_cost_opt('Rand-search-d3', title='Random search: Case 3', fig_num=1)
