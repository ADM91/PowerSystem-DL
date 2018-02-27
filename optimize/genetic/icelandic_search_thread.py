import numpy as np
from system.PowerSystem import PowerSystem
from system.pick_random_state import pick_random_state
from auxiliary.config_iceland import mp_opt
from system.combine_gen import combine_gen
import itertools
from optimize.genetic.evaluate_individual import evaluate_individual
from auxiliary.action_map import create_action_map


def icelandic_search_thread(ps_inputs, folder, save_data=1):

    # Instantiate system
    [metadata, spad_lim, verbose, verbose_state] = ps_inputs
    deactivated = np.random.choice(107 - 1, 4)  # Randomly choose 4 lines to deactivate
    ps = PowerSystem(metadata, spad_lim=spad_lim, deactivated=deactivated, verbose=verbose, verbose_state=verbose_state)

    # Set a base case (conditions must be met)
    count = 0
    while True:
        base_case = pick_random_state(ps.octave)
        base_case.gen, base_case.gencost = combine_gen(base_case.gen, base_case.gencost)
        base_result = ps.octave.runpf(base_case, mp_opt)
        ps.set_ideal_case(base_result)

        # Conditions: opf success, max 4 lines missing, no generators or loads missing
        a = ps.islands['0']['success'] == 1
        b = len(ps.action_list['dispatch load']) == 0
        c = len(ps.action_list['fixed load']) == 0
        d = len(ps.action_list['gen']) == 0
        e = len(ps.action_list['line']) <= 4
        f = count <= 10

        print([a,b,c,d,e])
        if a and b and c and d and e:
            break
        if count > 10:
            return

    # Generate permutation list
    indicies = np.arange(len(ps.action_list['line']))
    permutations = list(itertools.permutations(indicies))

    # Evaluate sequences, store best result
    action_map = create_action_map(ps.action_list)
    for seq in permutations:
        time_store, energy_store, cost_store, final_gene = evaluate_individual(ps, seq, action_map)



    # Save state-action pairs to file

    return