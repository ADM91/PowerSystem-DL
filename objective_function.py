import numpy as np
from oct2py import octave
from set_opf_constraints import set_opf_constraints
from restoration_time import restoration_time
from deviation_from_schedule import deviation_from_schedule
from deviation_from_losses import deviation_from_losses
from config import mp_opt


def objective_function(base_case_contingency, test_result_dist, ramp_rates, target_branch, max_SPA):
    """

    """

    # TODO: run a loop to solve all disconnected lines, restoration order must be an input

    # Run opf using the base case as setpoint reference, but has current topology!
    test_case_opf = set_opf_constraints(base_case_contingency, target_branch, max_SPA=max_SPA)
    test_result_opf = octave.runopf(test_case_opf, mp_opt)

    time = restoration_time(test_result_dist, test_result_opf, ramp_rates)
    power_deviation = deviation_from_schedule(base_case_contingency, test_result_dist, test_result_opf, ramp_rates)
    loss_deviation = deviation_from_losses()

    return time, power_deviation, loss_deviation

