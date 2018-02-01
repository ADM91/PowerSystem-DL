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


def optimization_parallel(ps_inputs, pop_size, iterations, i, eta, folder, save_data):

    np.random.seed()

    data = generate_dict(iterations, pop_size)

    # Unpack PowerSystem inputs
    [base_result, spad_lim, deactivated, verbose, verbose_state] = ps_inputs

    # Instantiate PowerSystem class
    ps = PowerSystem(base_result,
                     spad_lim=spad_lim,
                     deactivated=deactivated,
                     verbose=verbose,
                     verbose_state=verbose_state)

    action_map = create_action_map(ps.action_list)

    # Initialize population
    children = init_population(action_map, pop_size-1)
    fittest_individual = copy(children[0, :])

    # Initialize data store variables
    action_sequence_store = []
    total_cost_store = []
    best_total_cost_store = []

    # Run iterations
    for ii in range(iterations):

        print('\nOpt iter: %s GA iter %s\n' % (i, ii))

        population = np.vstack((fittest_individual, children))

        # Evaluate population
        cost_list = []
        for iii, individual in enumerate(population):
            time_store, energy_store, cost_store, final_gene = evaluate_individual(ps, individual, action_map)

            # replace gene with final gene
            population[iii] = final_gene

            cost_list.append(copy(cost_store['combined total']))

            # Save the individual data
            data['iter %s' % ii]['indiv %s' % iii]['cost'] = copy(cost_store)
            data['iter %s' % ii]['indiv %s' % iii]['energy'] = copy(energy_store)
            data['iter %s' % ii]['indiv %s' % iii]['time'] = copy(time_store)
            data['iter %s' % ii]['indiv %s' % iii]['sequence'] = copy(final_gene)

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

    # Save data dictionary to file!
    if save_data:
        with safe_open_w("data/%s/optimization_%s.pickle" % (folder, i), 'wb') as output_file:
            pickle.dump(data, output_file)




