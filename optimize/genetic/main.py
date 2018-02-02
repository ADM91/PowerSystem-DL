import numpy as np
from oct2py import octave
from auxiliary.config_case30 import mp_opt, deconstruct_2,\
    dispatchable_loads, ramp_rates, dispatch_load_cost, fixed_load_cost, loss_cost, disp_dev_cost
from optimize.genetic.genetic_alg_parallel import genetic_alg_parallel
from optimize.genetic.genetic_alg import genetic_alg
from system.PowerSystem import PowerSystem
from visualize.visualize_cost_ga import visualize_cost_ga
from visualize.visualize_cost_opt_ga import visualize_cost_opt_ga

# oct2py.utils.Oct2PyError: Octave evaluation error:
# error: makeAvl: For a dispatchable load, PG and QG must be consistent
#          with the power factor defined by PMIN and the Q limits.

metadata = [mp_opt,
            ramp_rates,
            dispatch_load_cost,
            fixed_load_cost,
            loss_cost,
            disp_dev_cost,
            dispatchable_loads]

# Instantiate PowerSystem object
np.set_printoptions(precision=2)
base_case = octave.loadcase('case30')
# base_case['branch'][:, 5] = line_ratings  # Only necessary for case 14
base_result = octave.runpf(base_case, mp_opt)
ps = PowerSystem(base_result,
                 metadata,
                 spad_lim=10,
                 deactivated=deconstruct_2,
                 verbose=0,
                 verbose_state=0)

# Run GA
cost_store, population, fittest_individual = genetic_alg(ps, n=10, iterations=20, eta=0.75)
visualize_cost_ga(cost_store[1:], 'asdf')


# Run GA parallel
np.set_printoptions(precision=2)
base_case = octave.loadcase('case30')
base_result = octave.runpf(base_case, mp_opt)
spad_lim = 10
deactivated = deconstruct_2
verbose = 0
verbose_state = 0
metadata = [mp_opt,
            ramp_rates,
            dispatch_load_cost,
            fixed_load_cost,
            loss_cost,
            disp_dev_cost,
            dispatchable_loads]
ps_inputs = [base_result, metadata, spad_lim, deactivated, verbose, verbose_state]
data = genetic_alg_parallel(ps_inputs,
                            pop_size=10,
                            iterations=5,
                            optimizations=1,
                            eta=0.75,
                            folder='test-ga',
                            save_data=1,
                            n_processes=1)

visualize_cost_opt_ga('/home/alexander/Documents/Thesis Work/PowerSystem-RL/data/test-ga', 'test-opt')
