

def execute_sequence(ps_obj, action_sequence):

    # Perform actions according to sequence
    states = []
    for action in action_sequence:
        action_type = action[0]
        index = action[1]

        if action_type == 'line':
            output = ps_obj.action_line(ps_obj.action_list['line'][index])
            if len(output) > 0:
                for state in output:
                    states.append(state)
            else:
                print('Line restoration failure: exiting')
                return []

        elif action_type == 'gen':
            output = ps_obj.action_gen(ps_obj.action_list['gen'][index])
            if len(output) > 0:
                for state in output:
                    states.append(state)
            else:
                print('Generator restoration failure: exiting')
                return []

        elif action_type == 'fixed load':
            output = ps_obj.action_fixed_load(ps_obj.action_list['fixed load'][index])
            if len(output) > 0:
                for state in output:
                    states.append(state)
            else:
                print('Fixed load restoration failure: exiting')
                return []

        elif action_type == 'dispatch load':
            output = ps_obj.action_dispatch_load(ps_obj.action_list['dispatch load'][index])
            if len(output) > 0:
                for state in output:
                    states.append(state)
            else:
                print('Dispatch load restoration failure: exiting')
                return []

        else:
            print('Error: action (%s) does not exist' % action[0])
            return []

    return states
