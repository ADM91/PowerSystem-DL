import numpy as np
from oct2py import octave
from auxiliary.config_case30 import mp_opt, deconstruct_6,\
    dispatchable_loads, ramp_rates, dispatch_load_cost, fixed_load_cost, loss_cost, disp_dev_cost
from optimize.genetic.genetic_alg_parallel import genetic_alg_parallel
from optimize.genetic.genetic_alg import genetic_alg
from system.PowerSystem import PowerSystem
from visualize.visualize_cost_ga import visualize_cost_ga
from visualize.visualize_cost_opt_ga import visualize_cost_opt_ga
from auxiliary.action_map import create_action_map
from system.execute_sequence import execute_sequence_2
from objective.objective_function import objective_function

# oct2py.utils.Oct2PyError: Octave evaluation error:
# error: makeAvl: For a dispatchable load, PG and QG must be consistent
#          with the power factor defined by PMIN and the Q limits.

metadata = {'mp_opt': mp_opt,
            'ramp_rates': ramp_rates,
            'dispatch_load_cost': dispatch_load_cost,
            'fixed_load_cost': fixed_load_cost,
            'loss_cost': loss_cost,
            'disp_dev_cost': disp_dev_cost,
            'gen_load_char': None,
            'dispatchable_loads': dispatchable_loads}

# Instantiate PowerSystem object
np.set_printoptions(precision=2)
base_case = octave.loadcase('case30')
# base_case['branch'][:, 5] = line_ratings  # Only necessary for case 14
base_result = octave.runpf(base_case, mp_opt)
ps = PowerSystem(base_result,
                 metadata,
                 spad_lim=10,
                 deactivated=deconstruct_6,
                 verbose=1,
                 verbose_state=0)


# seq = [7,8,3,1,0,13,9,10,12,6,11,2,5,4]
# action_map = create_action_map(ps.action_list)
# state_list, island_list = execute_sequence_2(ps, seq, action_map)
# time_store, energy_store, cost_store = objective_function(state_list, ps.ideal_state, metadata)


# for i, v in action_map.items():
#     print('%s: %s' % (i, v))
#
# print(cost_store['combined total'])



# # Run GA
# cost_store, population, fittest_individual = genetic_alg(ps, n=10, iterations=20, eta=0.75)
# visualize_cost_ga(cost_store[1:], 'asdf')


# Run GA parallel
np.set_printoptions(precision=5)
base_case = octave.loadcase('case30')
base_result = octave.runpf(base_case, mp_opt)
spad_lim = 10
deactivated = deconstruct_6
verbose = 0
verbose_state = 0
metadata = {'mp_opt': mp_opt,
            'ramp_rates': ramp_rates,
            'dispatch_load_cost': dispatch_load_cost,
            'fixed_load_cost': fixed_load_cost,
            'loss_cost': loss_cost,
            'disp_dev_cost': disp_dev_cost,
            'gen_load_char': None,
            'dispatchable_loads': dispatchable_loads}
ps_inputs = [base_result, metadata, spad_lim, deactivated, verbose, verbose_state]
data = genetic_alg_parallel(ps_inputs,
                            pop_size=15,
                            iterations=10,
                            optimizations=4,
                            eta=0.75,
                            folder='ga-eta75-d6-test',
                            save_data=1,
                            n_processes=4)

visualize_cost_opt_ga('/home/alexander/Documents/Thesis Work/PowerSystem-RL/data/ga-eta75-d6', 'test-opt')


# For printing latex format:
for i in ps.ideal_case['branch'][:, [0, 1, 2, 3, 13, 14, 5]]:
    print('%d - %d & %.2f & %.2f & %.2f & %.2f & %d' % tuple(i))

# Generators
for i in ps.ideal_case['gen'][:, [0, 1, 2, 8, 3, 4]]:
    print('%d & %.2f & %.2f & %d & %d & %d\\\\' % tuple(i))

# Fixed loads
for i in ps.ideal_case['bus'][:, [0, 2, 3]]:
    if i[1] != 0 or i[2] !=0:
        print('%d & %.1f & %.1f\\\\' % tuple(i))

# Dispatchable loads
for i in ps.ideal_case['gen'][:, [0, 9, 4]]:
    if i[1] < 0:
        print('%d & %.1f & %.1f\\\\' % tuple(i))
