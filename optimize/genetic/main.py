import numpy as np
from oct2py import octave
from system.PowerSystem import PowerSystem
from auxiliary.config import mp_opt, line_ratings, deconstruct_3
from tree.RestorationTreeParallel import create_shared_root
from copy import deepcopy
from auxiliary.action_map import create_action_map
from optimize.genetic.init_population import init_population
from optimize.genetic.evaluate_individual import evaluate_individual
from optimize.genetic.genetic_alg import genetic_alg
from optimize.genetic.genetic_alg_parallel import genetic_alg_parallel
from visualize.visualize_cost_ga import visualize_cost_ga

# Instantiate PowerSystem object
np.set_printoptions(precision=2)
base_case = octave.loadcase('case14')
base_case['branch'][:, 5] = line_ratings  # Have to add line ratings
base_result = octave.runpf(base_case, mp_opt)
ps = PowerSystem(base_result,
                 spad_lim=10,
                 deactivated=deconstruct_3,
                 verbose=0,
                 verbose_state=0)

# Run GA
cost_store, population, fittest_individual = genetic_alg(ps, n=10, iterations=20)


# Run GA parallel
np.set_printoptions(precision=2)
base_case = octave.loadcase('case14')
base_case['branch'][:, 5] = line_ratings  # Have to add line ratings
base_result = octave.runpf(base_case, mp_opt)
spad_lim = 10
deactivated = deconstruct_3
verbose = 0
verbose_state = 0
ps_inputs = [base_result, spad_lim, deactivated, verbose, verbose_state]
data = genetic_alg_parallel(ps_inputs,
                            pop_size=4,
                            iterations=3,
                            optimizations=2,
                            eta=0.5,
                            folder='test',
                            save_data=0,
                            n_processes=3)

visualize_cost_ga(cost_store, 'n=10, iter=50')


