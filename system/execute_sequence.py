from auxiliary.iterable import iterable
from system.verify_state_feasibility import verify_state_feasibility

def execute_sequence(ps_obj, action_sequence):

    # Perform actions according to sequence
    states = []
    for i, action in enumerate(action_sequence):
        action_type = action[0]
        index = action[1]

        if action_type == 'line':
            output = ps_obj.action_line(ps_obj.action_list['line'][index])
            if len(output) > 0:
                for state in output:
                    states.append(state)
            else:
                print('Line restoration failure: exiting')
                return ['fail', i]

        elif action_type == 'gen':
            output = ps_obj.action_gen(ps_obj.action_list['gen'][index])
            if len(output) > 0:
                for state in output:
                    states.append(state)
            else:
                print('Generator restoration failure: exiting')
                return ['fail', i]

        elif action_type == 'fixed load':
            output = ps_obj.action_fixed_load(ps_obj.action_list['fixed load'][index])
            if len(output) > 0:
                for state in output:
                    states.append(state)
            else:
                print('Fixed load restoration failure: exiting')
                return ['fail', i]

        elif action_type == 'dispatch load':
            output = ps_obj.action_dispatch_load(ps_obj.action_list['dispatch load'][index])
            if len(output) > 0:
                for state in output:
                    states.append(state)
            else:
                print('Dispatch load restoration failure: exiting')
                return ['fail', i]

        else:
            print('Error: action (%s) does not exist' % action[0])
            return []

    return states


def execute_sequence_2(ps_obj, sequence, action_map):

    # Perform actions according to sequence and action map
    state_list = list()
    island_list = list()
    for action in iterable(sequence):
        action_type = action_map[action][0]
        buses = action_map[action][1]

        if action_type == 'line':

            sl, il = ps_obj.action_line(buses)
            if len(sl) > 0:
                for s, l in zip(sl, il):
                    state_list.append(s)
                    island_list.append(l)
            else:
                print('Line restoration failure: exiting')
                return [], []

        elif action_type == 'gen':
            sl, il = ps_obj.action_gen(buses)
            if len(sl) > 0:
                for s, l in zip(sl, il):
                    state_list.append(s)
                    island_list.append(l)
            else:
                print('Generator restoration failure: exiting')
                return [], []

        elif action_type == 'fixed load':
            sl, il = ps_obj.action_fixed_load(buses)
            if len(sl) > 0:
                for s, l in zip(sl, il):
                    state_list.append(s)
                    island_list.append(l)
            else:
                print('Fixed load restoration failure: exiting')
                return [], []

        elif action_type == 'dispatch load':
            sl, il = ps_obj.action_dispatch_load(buses)
            if len(sl) > 0:
                for s, l in zip(sl, il):
                    state_list.append(s)
                    island_list.append(l)
            else:
                print('Dispatch load restoration failure: exiting')
                return [], []

        else:
            print('Error: action (%s) does not exist' % action[0])
            return [], []


    return state_list, island_list
