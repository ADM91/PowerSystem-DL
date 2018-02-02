from optimize.genetic.init_population import init_population
from optimize.genetic.mutate import mutate
from optimize.genetic.crossover import crossover
from optimize.genetic.evaluate_individual import evaluate_individual
from optimize.genetic.selection import selection
from auxiliary.action_map import create_action_map
import numpy as np
from copy import copy


def genetic_alg(ps, n, iterations, eta):

    action_map = create_action_map(ps.action_list)

    # Initialize population
    children = init_population(action_map, n-1)
    fittest_individual = copy(children[0, :])

    cost_store_array = np.empty((iterations, n))

    # Run iterations
    for i in range(iterations):

        print('\nGA Iteration %s\n' % i)

        population = np.vstack((fittest_individual, children))

        # Evaluate population
        cost_list = []
        for ii, individual in enumerate(population):
            time_store, energy_store, cost_store, final_gene = evaluate_individual(ps, individual, action_map)

            # replace gene with final gene
            population[ii] = final_gene
            cost_list.append(cost_store['combined total'])

        # Store cost data
        print('population: \n%s\n' % np.sort(cost_list))
        cost_store_array[i, :] = np.array(cost_list)

        # Selection
        pairs = selection(n-1, cost_list)

        # Crossover
        children = crossover(pairs, population)

        # Mutation
        children = mutate(children, eta)

        # Elitism
        fittest_individual = copy(population[np.argmin(cost_list), :])

    return cost_store_array, population, fittest_individual
