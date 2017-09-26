

def restore_power_system(ps, action_sequence):
    """ This function needs to restore the power grid one step at a time. The steps are
    provided ahead of time by the optimizer.

    Specificly this function includes:

    a) if an action leads to opf convergence failure, the restoration has failed, exit function

    b) need to be aware if reinstating a line connects islands. So islands can be joined
       into a single case structure.

    c) reconnecting islands we assume is a free task, the operators can make small adjustments
       to synchronize the systems

    d) the action sequence is a list of indices to the disconnected elements dictionary

      """

    for action in action_sequence:

        if action[0] == 'lines':
            ps.action_line(action[1])
        elif action[0] == 'fixed loads':
            ps.action_load(action[1])
        elif action[0] == 'generators':
            ps.action_gen(action[1])
        else:
            print('action error')
            break

