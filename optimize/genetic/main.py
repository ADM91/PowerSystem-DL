import numpy as np
from oct2py import octave
from auxiliary.config_case30 import mp_opt, deconstruct_6,\
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
                 deactivated=deconstruct_6,
                 verbose=1,
                 verbose_state=0)
#
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
                            iterations=10,
                            optimizations=20,
                            eta=0.5,
                            folder='ga-eta-5',
                            save_data=1,
                            n_processes=3)

# visualize_cost_opt_ga('/home/alexander/Documents/Thesis Work/PowerSystem-RL/data/test', 'test-opt')


# Errors during optimization:


# Error: Octave evaluation error:
# error: makeAvl: For a dispatchable load, PG and QG must be consistent
#          with the power factor defined by PMIN and the Q limits.

# (problem is that the previous restoration action leaves system in impossible state. Need to catch
# these situations before the restoration continues.  Sometimes getting negative generation and positive d-loads)
# (Also try setting PMIN, QMIN < 0 , might enforce pf constraint better )


# Fairly common:
#   File "/home/alexander/Documents/Thesis Work/PowerSystem-RL/optimize/genetic/evaluate_individual.py", line 45, in evaluate_individual
#     val = init_gene[0]
# IndexError: list index out of range

# General bug in the feasibility preserving evaluation code.


# Aslo still have the dimension mismatch warnings, very common

