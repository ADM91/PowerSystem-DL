

def deviation_from_schedule(base_case_contingency, test_result_dist, test_result_opf, ramp_rates):
    """
    Solves for the sum deviation from base case generator schedule during the ramping
    period prior to reconnection.  Units come out to MW*min.

    :param base_case_contingency:
    :param test_result_dist:
    :param test_result_opf:
    :param ramp_rates:
    :return:
    """

    # Establish base
    base = base_case_contingency['gen'][:, 1]

    # Calculate deviation



    return power_deviation