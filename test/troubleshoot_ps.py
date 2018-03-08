import numpy as np
from oct2py import octave
from auxiliary.config_iceland import mp_opt,\
    dispatchable_loads,\
    ramp_rates,\
    dispatch_load_cost,\
    fixed_load_cost,\
    loss_cost,\
    disp_dev_cost, \
    load_cost,\
    subset_branches_ind
import numpy as np
from system.PowerSystem import PowerSystem
from optimize.genetic.init_population import init_population
from optimize.genetic.crossover import crossover
from optimize.genetic.evaluate_individual import evaluate_individual
from optimize.genetic.selection import selection
from optimize.genetic.mutate import mutate
from copy import copy, deepcopy
from system.pick_random_state import pick_random_state
from auxiliary.config_iceland import mp_opt
from system.combine_gen import combine_gen
from system.combine_lines import combine_lines
from auxiliary.action_map import create_action_map


# Corner case:  Buses not on action list! - two lines are connected to same buses.
# deactivated = [84, 89, 66, 65]
# deactivated = [61, 59, 85, 87]
deactivated = [55, 89, 88, 57]
np.random.seed()
# deactivated = np.random.choice(subset_branches_ind, 4, replace=False)  # Randomly choose 4 lines to deactivate


# Find case on icelandic system where disconnected lines does not match
np.set_printoptions(precision=2)
base_case = octave.loadcase('/home/alexander/Documents/MATLAB/alex parser/MPCfiles/PSSE_Landsnet_19_06_2017__22_03_32.mat')
base_case.gen, base_case.gencost = combine_gen(base_case.gen, base_case.gencost)
base_case.branch = combine_lines(base_case.branch)
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

ps = PowerSystem(metadata, spad_lim=spad_lim, deactivated=deactivated, verbose=verbose,
                 verbose_state=verbose_state)
# base_case = pick_random_state(ps.octave)
# base_case.gen, base_case.gencost = combine_gen(base_case.gen, base_case.gencost)
base_result = ps.octave.runpf(base_case, mp_opt)
success = ps.set_ideal_case(base_result)

print(deactivated)
for k in ps.action_list.keys():
    print(k,ps.action_list[k])

# GA
pop_size = 4
iterations = 3
eta = 0.9

# Initialize population
action_map = create_action_map(ps.action_list)
children = init_population(action_map, pop_size - 1)
fittest_individual = copy(children[0, :])

# Initialize data store variables
action_sequence_store = []
total_cost_store = []
best_total_cost_store = []


# Run generation

population = np.vstack((fittest_individual, children))

# Evaluate population
cost_list = []
individual = population[0]
for iii, individual in enumerate(population):
    actions = [action_map[ind] for ind in individual]
    print('evaluating: %s' % actions)
    time_store, energy_store, cost_store, final_gene = evaluate_individual(ps, individual, action_map)
    if len(final_gene) == 0:
        print('\nFailed to find a feasible sequence\n')
        if iii > 3:
            # Mutate an already existing successful gene
            individual = mutate(population[iii-1, :].reshape(1, -1), 1)
            time_store, energy_store, cost_store, final_gene = evaluate_individual(ps, individual, action_map)
    else:
        pass

    # replace gene with final gene
    population[iii] = final_gene

    cost_list.append(copy(cost_store['combined total']))

    # Save the individual data
    # data['iter %s' % ii]['indiv %s' % iii]['cost'] = copy(cost_store)
    # data['iter %s' % ii]['indiv %s' % iii]['energy'] = copy(energy_store)
    # data['iter %s' % ii]['indiv %s' % iii]['time'] = copy(time_store)
    # data['iter %s' % ii]['indiv %s' % iii]['sequence'] = copy(final_gene)

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
pairs = selection(pop_size - 1, cost_list)

# Crossover
children = crossover(pairs, population)

# Mutation
children = mutate(children, eta)

# Elitism
fittest_individual = copy(population[np.argmin(cost_list), :])

# Store key opt data
# action_sequence_store.append(copy(fittest_individual))  # only storing sequence of fittest individual
# total_cost_store.append(copy(cost_list))
# best_total_cost_store.append(np.min(cost_list))