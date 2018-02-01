import numpy as np
from oct2py import octave
from auxiliary.config_case30 import mp_opt, deconstruct_1,\
    dispatchable_loads, ramp_rates, dispatch_load_cost, fixed_load_cost, loss_cost, disp_dev_cost
from optimize.genetic.genetic_alg_parallel import genetic_alg_parallel
from optimize.genetic.genetic_alg import genetic_alg
from system.PowerSystem import PowerSystem

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
                 deactivated=deconstruct_1,
                 verbose=0,
                 verbose_state=0)

# Run GA
cost_store, population, fittest_individual = genetic_alg(ps, n=10, iterations=3)


# Run GA parallel
np.set_printoptions(precision=2)
base_case = octave.loadcase('case14')
# base_case['branch'][:, 5] = line_ratings  # Only necessary for case 14
base_result = octave.runpf(base_case, mp_opt)
spad_lim = 10
deactivated = deconstruct_1
verbose = 0
verbose_state = 0
ps_inputs = [base_result, spad_lim, deactivated, verbose, verbose_state]
data = genetic_alg_parallel(ps_inputs,
                            pop_size=10,
                            iterations=20,
                            optimizations=10,
                            eta=0.5,
                            folder='test-ga',
                            save_data=1,
                            n_processes=3)

# visualize_cost_ga(cost_store, 'n=10, iter=50')


