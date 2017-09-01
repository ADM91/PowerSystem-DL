

def set_SPA(test_case):
    """
    This will set buses on either side of a faulted line as PV buses,
    this way regular power flow solves the problemo... no it doesn't...
    Regular power flow will not solve the generation redispatch, it will
    alter the voltage angles at other buses.  So setting a buses on faulted
    lines to PV assumes there is a voltage control resource at the bus.  I
    guess I'll have to learn optimal power flow thoroughly!
    :param test_case:
    :return:
    """
    pass