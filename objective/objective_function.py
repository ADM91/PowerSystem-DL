import numpy as np
from copy import deepcopy
from objective.cumulative_losses import cumulative_losses
from objective.cumulative_power_deviation import cumulative_power_deviation
from objective.cumulative_lost_load import cumulative_lost_load
from objective.action_time import action_time


def objective_function(state_list, ideal_state, md):

    time_store = []
    energy_store = {'lost load': [],
                    'losses': [],
                    'dispatch deviation': []}
    cost_store = {'lost load': [],
                  'losses': [],
                  'dispatch deviation': [],
                  'total': [],
                  'combined total': None}

    # Ideal state values
    ideal_losses = deepcopy(ideal_state['losses'])
    ideal_gen = deepcopy(ideal_state['real gen'][:, 1])
    ideal_fixed = deepcopy(ideal_state['fixed load'][:, 1])
    ideal_dispatched = deepcopy(-ideal_state['dispatch load'][:, 1])

    for i in range(1, len(state_list)):

        state_1 = state_list[i-1]
        state_2 = state_list[i]

        # States are repeated between actions, leave these out of cost calc
        if np.any(state_1['real inj'] != state_2['real inj']):

            # Evaluate energy lost over time period
            time = action_time(state_1, state_2, md['ramp_rates'])
            [lost_d_load, lost_f_load] = cumulative_lost_load(state_1, state_2, ideal_fixed, ideal_dispatched, time)
            losses = cumulative_losses(state_1, state_2, time, ideal_losses)
            dispatch_dev = cumulative_power_deviation(ideal_gen, state_1, state_2, time)

            # Store time of action
            time_store.append(time)

            # Store energy values
            energy_store['lost load'].append([lost_d_load, lost_f_load])
            energy_store['losses'].append(losses)
            energy_store['dispatch deviation'].append(dispatch_dev)

            # Calculate and store objective of lost energy
            cost_a = np.sum(lost_d_load*md['dispatch_load_cost']) + np.sum(lost_f_load*md['fixed_load_cost'])
            cost_b = losses*md['loss_cost']
            cost_c = dispatch_dev*md['disp_dev_cost']
            cost_store['lost load'].append(cost_a)
            cost_store['losses'].append(cost_b)
            cost_store['dispatch deviation'].append(cost_c)
            cost_store['total'].append(np.sum([cost_a, cost_b, cost_c]))
        else:

            # Store time of action
            time_store.append(0)

            # Store energy values
            energy_store['lost load'].append(0)
            energy_store['losses'].append(0)
            energy_store['dispatch deviation'].append(0)

            # Calculate and store objective of lost energy
            cost_store['lost load'].append(0)
            cost_store['losses'].append(0)
            cost_store['dispatch deviation'].append(0)
            cost_store['total'].append(0)

    cost_store['combined total'] = np.sum(cost_store['total'])

    return time_store, energy_store, cost_store

