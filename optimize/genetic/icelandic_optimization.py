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
    load_cost,\
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
verbose = 0
verbose_state = 0
metadata = {'mp_opt': mp_opt,
            'ramp_rates': ramp_rates,
            'dispatch_load_cost': dispatch_load_cost,
            'fixed_load_cost': fixed_load_cost,
            'loss_cost': loss_cost,
            'disp_dev_cost': disp_dev_cost,
            'gen_load_char': gen_load_char,
            'dispatchable_loads': dispatchable_loads,
            'load_cost': load_cost}
ps_inputs = [metadata, spad_lim, verbose, verbose_state, subset_branches_ind]

# for i in range(5):
data = genetic_alg_parallel(ps_inputs,
                            pop_size=10,
                            iterations=10,
                            optimizations=3,
                            eta=0.9,
                            folder='iceland_test_2',
                            save_data=1,
                            n_processes=3,
                            fun=icelandic_optimization_thread)


# --------------- Visualize state ---------------

from oct2py import octave
from auxiliary.config_case30 import mp_opt, deconstruct_6,\
    dispatchable_loads, ramp_rates, dispatch_load_cost, fixed_load_cost, loss_cost, disp_dev_cost
from system.PowerSystem import PowerSystem
from system.execute_sequence import execute_sequence_2
from objective.objective_function import objective_function
from visualize.visualize_state import visualize_state
from visualize.visualize_cost import visualize_cost
import pickle
import numpy as np
from objective.power_deviation import power_deviation


with open('/home/alexander/Documents/Thesis Work/PowerSystem-RL/data/iceland_test_2/optimization_0.pickle', 'rb') as f:
    data = pickle.load(f)
sequence = data['action_sequence_store'][-1]
action_map = data['action map']
metadata = data['metadata']
spad_lim = data['spad_lim']
deactivated = data['deactivated']
base = data['base_result']

ps = PowerSystem(metadata, spad_lim=spad_lim, deactivated=deactivated, verbose=0,
                 verbose_state=0)
success = ps.set_ideal_case(base)

state_list, island_list = execute_sequence_2(ps, sequence, action_map)
time_store, energy_store, cost_store = objective_function(state_list, ps.ideal_state, metadata)
[gen_dev, load_dev, loss_dev] = power_deviation(state_list, ps.ideal_state)

# visualize_state(ps.ideal_case, ps.ideal_state, state_list, fig_num=1, frames=10, save=False)
visualize_cost(time_store, cost_store, energy_store, gen_dev, load_dev, loss_dev)

print([action_map[act] for act in sequence])





