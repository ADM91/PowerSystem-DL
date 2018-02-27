from optimize.stochastic.stochastic_tree_search_action_limit import stochastic_tree_search_action_limit
from tree.RestorationTree import RestorationTree
import numpy as np
from oct2py import octave
from auxiliary.config_case30 import mp_opt, deconstruct_6,\
    dispatchable_loads, ramp_rates, dispatch_load_cost, fixed_load_cost, loss_cost, disp_dev_cost
from system.PowerSystem import PowerSystem


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
                 verbose=0,
                 verbose_state=0)

tree = RestorationTree(ps)
stochastic_tree_search_action_limit(ps, tree,
                                    opt_iteration=20,
                                    action_limit=2100,
                                    method='uniform',
                                    verbose=1,
                                    save_data=1,
                                    folder='ts-uniform-d6')



