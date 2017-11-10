from copy import deepcopy
import numpy as np
from oct2py import octave
from auxiliary.config import case14_ramp_rates, dispatch_load_cost, fixed_load_cost, loss_cost, disp_dev_cost
from auxiliary.set_opf_constraints import set_opf_constraints
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
        print(i)

        state_1 = state_list[i-1]
        state_2 = state_list[i]

        # Evaluate energy lost over time period
        time = ramp_time(state_1, state_2, case14_ramp_rates)
        [lost_d_load, lost_f_load] = cumulative_lost_load(state_1, state_2, ideal_fixed, ideal_dispatched, time)
        losses = cumulative_losses(state_1, state_2, time, ideal_losses)
        dispatch_dev = cumulative_power_deviation(ideal_gen, state_1, state_2, ramp_time)

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


# def objective_function(base_case_contingency, result, ramp_rates, order, slack_ind, max_SPA):
#     """
#
#     :param base_case_contingency: Case containing original generator schedule and faulted branches
#     :param result: Solved case
#     :param ramp_rates:
#     :param order:
#     :param slack_ind:
#     :param max_SPA:
#     :return:
#     """
#
#     # Work with a copy of the base case with contingencies
#     base_case = deepcopy(base_case_contingency)
#
#     # Initiate cost variables
#     cum_ramp_time = 0
#     cum_power_deviation = 0
#     cum_losses = 0
#
#     # Set print format for numpy arrays
#     np.set_printoptions(formatter={'float': '{: 0.3f}'.format})
#
#     # Restore lines and calculate cumulative cost (ramp time, power deviation, and MW losses)
#     for branch in order:
#
#         # Run opf using the base case as setpoint reference, but has current topology!
#         opf_case = set_opf_constraints(base_case, branch, max_SPA=max_SPA)
#         # Prints the case SPA limits
#         if mode is 'debug':
#             print(opf_case['branch'][:, 11:13])
#         opf_result = octave.runopf(opf_case, mp_opt)
#         # Prints the deviation from generation schedule
#         if mode is 'debug':
#             print(opf_result['gen'][:, 1:3] - base_case['gen'][:, 1:3])
#
#         # Calculate cost parameters
#         ramp_time = restoration_time(result, opf_result, ramp_rates)
#         cum_ramp_time += ramp_time
#         cum_power_deviation += cumulative_power_deviation(base_case, result, opf_result, ramp_time)
#         cum_losses += cumulative_losses(result, opf_result, ramp_time)
#
#         # Update base case: branch has been restored
#         base_case['branch'][branch, 10] = 1
#         base_case['branch'][branch, 11:13] = [-360, 360]
#
#         # Update case result: power has been re-dispatched according to opf solution and branch restored
#         opf_result['branch'][branch, 10] = 1
#         result = opf_result
#
#         # I don't have to redistribute slack pickup if I assume we move immediately to the next
#         # generation dispatch.
#
#     return cum_ramp_time, cum_power_deviation, cum_losses
