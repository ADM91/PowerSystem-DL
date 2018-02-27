import numpy as np
from oct2py import octave
from auxiliary.config_iceland import mp_opt,\
    dispatchable_loads,\
    ramp_rates,\
    dispatch_load_cost,\
    fixed_load_cost,\
    loss_cost,\
    disp_dev_cost, \
    gen_load_char,\
    line_map,\
    subset_branches_ind
from system.PowerSystem import PowerSystem
from system.pick_random_state import pick_random_state
from system.combine_gen import combine_gen
from optimize.genetic.genetic_alg_parallel import genetic_alg_parallel
from optimize.genetic.icelandic_optimization_thread import icelandic_optimization_thread


# Run GA parallel
np.set_printoptions(precision=5)
base_case = pick_random_state(octave)
base_case.gen, base_case.gencost = combine_gen(base_case.gen, base_case.gencost)

base_result = octave.runpf(base_case, mp_opt)
spad_lim = 20
# deactivated = np.random.choice(107-1, 4)
verbose = 0
verbose_state = 0
metadata = {'mp_opt': mp_opt,
            'ramp_rates': ramp_rates,
            'dispatch_load_cost': dispatch_load_cost,
            'fixed_load_cost': fixed_load_cost,
            'loss_cost': loss_cost,
            'disp_dev_cost': disp_dev_cost,
            'gen_load_char': gen_load_char,
            'dispatchable_loads': dispatchable_loads}
ps_inputs = [metadata, spad_lim, verbose, verbose_state, subset_branches_ind]
data = genetic_alg_parallel(ps_inputs,
                            pop_size=5,
                            iterations=3,
                            optimizations=1,
                            eta=0.75,
                            folder='iceland_test',
                            save_data=1,
                            n_processes=1,
                            fun=icelandic_optimization_thread)
