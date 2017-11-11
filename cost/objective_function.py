import numpy as np
from auxiliary.config import case14_ramp_rates, dispatch_load_cost, fixed_load_cost, loss_cost, disp_dev_cost
from cost.cumulative_losses import cumulative_losses
from cost.cumulative_power_deviation import cumulative_power_deviation
from cost.cumulative_lost_load import cumulative_lost_load
from cost.ramp_time import ramp_time


def objective_function(state_list, ideal_state):

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
    ideal_losses = ideal_state['losses']
    ideal_gen = ideal_state['real gen'][:, 1]
    ideal_fixed = ideal_state['fixed load'][:, 1]
    ideal_dispatched = -ideal_state['dispatch load'][:, 1]

    for i in range(1, len(state_list)):

        state_1 = state_list[i-1]
        state_2 = state_list[i]

        # Evaluate energy lost over time period
        time = ramp_time(state_1, state_2, case14_ramp_rates)
        [lost_d_load, lost_f_load] = cumulative_lost_load(state_1, state_2, ideal_fixed, ideal_dispatched, time)
        losses = cumulative_losses(state_1, state_2, time, ideal_losses)
        dispatch_dev = cumulative_power_deviation(ideal_gen, state_1, state_2, time)

        # Store time of action
        time_store.append(time)

        # Store energy values
        energy_store['lost load'].append([lost_d_load, lost_f_load])
        energy_store['losses'].append(losses)
        energy_store['dispatch deviation'].append(dispatch_dev)

        # Calculate and store cost of lost energy
        cost_a = np.sum(lost_d_load*dispatch_load_cost) + np.sum(lost_f_load*fixed_load_cost)
        cost_b = losses*loss_cost
        cost_c = dispatch_dev*disp_dev_cost
        cost_store['lost load'].append(cost_a)
        cost_store['losses'].append(cost_b)
        cost_store['dispatch deviation'].append(cost_c)
        cost_store['total'].append(np.sum([cost_a, cost_b, cost_c]))

    cost_store['combined total'] = np.sum(cost_store['total'])

    return time_store, energy_store, cost_store

