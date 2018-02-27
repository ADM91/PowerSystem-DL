import numpy as np
from system.PowerSystem import PowerSystem
from auxiliary.action_map import create_action_map
from optimize.genetic.init_population import init_population
from optimize.genetic.crossover import crossover
from optimize.genetic.evaluate_individual import evaluate_individual
from optimize.genetic.selection import selection
from optimize.genetic.mutate import mutate
from copy import copy, deepcopy
from optimize.generate_dict import generate_dict
from auxiliary.open_path import safe_open_w
import pickle
from system.pick_random_state import pick_random_state
from auxiliary.config_iceland import mp_opt
from system.combine_gen import combine_gen


def icelandic_optimization_thread(ps_inputs, pop_size, iterations, i, eta, folder, save_data):

    np.random.seed()

    data = generate_dict(iterations, pop_size)

    # Instantiate a randomized system state and degradation
    [metadata, spad_lim, verbose, verbose_state, subset_branches_ind] = ps_inputs
    while True:
        # Instantiate PowerSystem class
        print('instantiating power system')
        deactivated = np.random.choice(subset_branches_ind, 4)  # Randomly choose 4 lines to deactivate
        ps = PowerSystem(metadata, spad_lim=spad_lim, deactivated=deactivated, verbose=verbose,
                         verbose_state=verbose_state)
        base_case = pick_random_state(ps.octave)
        base_case.gen, base_case.gencost = combine_gen(base_case.gen, base_case.gencost)
        base_result = ps.octave.runpf(base_case, mp_opt)
        success = ps.set_ideal_case(base_result)
        ps.reset()

        # make sure there aren't too many missing elements
        n_actions = len(ps.action_list['line']) + len(ps.action_list['dispatch load']) + len(ps.action_list['fixed load']) + len(ps.action_list['gen'])
        a = n_actions < 10
        b = len(ps.action_list['line']) >= 4
        print('number of actions: %s' % n_actions)
        print('base case success: %s' % success)
        print('lines deactivated: %s' % len(ps.action_list['line']))
        if a and b and success:
            break

    # print(ps.action_list)

    action_map = create_action_map(ps.action_list)
    data['action map'] = action_map

    # Initialize population
    children = init_population(action_map, pop_size-1)
    fittest_individual = copy(children[0, :])

    # Initialize data store variables
    action_sequence_store = []
    total_cost_store = []
    best_total_cost_store = []

    # Run generations
    for ii in range(iterations):

        population = np.vstack((fittest_individual, children))

        # Evaluate population
        cost_list = []
        for iii, individual in enumerate(population):
            actions = [action_map[ind] for ind in individual]
            print('evaluating: %s' % actions)
            time_store, energy_store, cost_store, final_gene = evaluate_individual(ps, individual, action_map)
            if cost_store['combined total'] == np.nan:
                print('\nGetting nans in output!!!!')
                print(time_store)
                print(energy_store)
                print(cost_store)
                print('\n')

            # replace gene with final gene
            population[iii] = final_gene

            cost_list.append(copy(cost_store['combined total']))

            # Save the individual data
            data['iter %s' % ii]['indiv %s' % iii]['cost'] = copy(cost_store)
            data['iter %s' % ii]['indiv %s' % iii]['energy'] = copy(energy_store)
            data['iter %s' % ii]['indiv %s' % iii]['time'] = copy(time_store)
            data['iter %s' % ii]['indiv %s' % iii]['sequence'] = copy(final_gene)

        # Print cost of each individual
        order = np.argsort(cost_list)
        cost_list = np.array(cost_list)
        # print(order)
        # print(cost_list)
        # print(population)
        print('\nOpt iter: %s GA gen %s' % (i, ii))
        print('population fitness: \n%s\n' % cost_list[order])
        print('population genes:\n%s\n' % population[order])

        # Selection
        pairs = selection(pop_size-1, cost_list)

        # Crossover
        children = crossover(pairs, population)

        # Mutation
        children = mutate(children, eta)

        # Elitism
        fittest_individual = copy(population[np.argmin(cost_list), :])

        # Store key opt data
        action_sequence_store.append(copy(fittest_individual))  # only storing sequence of fittest individual
        total_cost_store.append(copy(cost_list))
        best_total_cost_store.append(np.min(cost_list))

    # Save the key opt data
    data['action_sequence_store'] = action_sequence_store
    data['total_cost_store'] = total_cost_store
    data['best_total_cost_store'] = best_total_cost_store
    data['metadata'] = ps.metadata
    data['spad_lim'] = ps.spad_lim
    data['deactivated'] = ps.deactivated
    data['base_result'] = base_result

    # Save data dictionary to file!
    if save_data:
        with safe_open_w("data/%s/optimization_%s.pickle" % (folder, i), 'wb') as output_file:
            pickle.dump(data, output_file)
