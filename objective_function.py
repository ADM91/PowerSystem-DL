import numpy as np
from oct2py import octave
from set_opf_constraints import set_opf_constraints
from restoration_time import restoration_time
from cumulative_power_deviation import cumulative_power_deviation
from cumulative_losses import cumulative_losses
from distribute_slack import distribute_slack
from config import mp_opt, case14_droop_constants, distribute_slack_constants


def objective_function(base_case_contingency, result, ramp_rates, order, slack_ind, max_SPA):
    """

    :param base_case_contingency: Case containing original generator schedule and faulted branches
    :param result: Solved case
    :param ramp_rates:
    :param order:
    :param slack_ind:
    :param max_SPA:
    :return:
    """

    # Initiate cost variables
    cum_ramp_time = 0
    cum_power_deviation = 0
    cum_losses = 0

    # Restore lines and calculate cumulative cost (ramp time, power deviation, and MW losses)
    for branch in order:

        # Run opf using the base case as setpoint reference, but has current topology!
        opf_case = set_opf_constraints(base_case_contingency, branch, max_SPA=max_SPA)
        opf_result = octave.runopf(opf_case, mp_opt)

        # Calculate cost parameters
        ramp_time = restoration_time(result, opf_result, ramp_rates)
        cum_ramp_time += ramp_time
        cum_power_deviation += cumulative_power_deviation(base_case_contingency, result, opf_result, ramp_time)
        cum_losses += cumulative_losses(result, opf_result, ramp_time)

        # Update base case: branch has been restored
        base_case_contingency['branch'][branch] = 1

        # Update case result: power has been re-dispatched according to opf solution and branch restored
        opf_result['branch'][branch, 10] = 1
        result = opf_result
        # result = distribute_slack(test_case=opf_result,
        #                           slack_ind=slack_ind,
        #                           droop_constants=case14_droop_constants,
        #                           converge_options=distribute_slack_constants)

    return cum_ramp_time, cum_power_deviation, cum_losses
