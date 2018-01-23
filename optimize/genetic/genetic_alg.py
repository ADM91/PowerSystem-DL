from optimize.genetic.init_population import init_population
from optimize.genetic.mutate import mutate
from optimize.genetic.crossover import crossover
from optimize.genetic.feasibility_preservation import feasibility_preservation
from optimize.genetic.evaluate_individual import evaluate_individual
from auxiliary.action_map import create_action_map


def genetic_alg(ps, tree):

    action_map = create_action_map(ps.action_list)

    # Initialize population
    init_pop = init_population(action_map, n)

    # Evaluate population
    fitness = []
    for individual in init_pop:
        fitness.append(evaluate_individual(ps, tree, individual))





    pass