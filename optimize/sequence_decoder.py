import numpy as np


def decode_sequence(action_list, sequence):

    n_actions = int(np.sum([len(item) for item in action_list.values()]))
    if len(sequence) != n_actions:
        print('Error: sequence length is %d for %d available actions' % (len(sequence), n_actions))
        return

    # Find number of each action type
    len_a = len(action_list['line'])
    len_b = len(action_list['gen'])
    len_c = len(action_list['fixed load'])
    len_d = len(action_list['dispatch load'])

    # Generate action sequence
    action_sequence = []
    for i in range(n_actions):
        if sequence[i] <= len_a - 1:
            index = sequence[i]
            action_sequence.append(['line', index])
        elif sequence[i] <= len_a + len_b - 1:
            index = sequence[i] - len_a
            action_sequence.append(['gen', index])
        elif sequence[i] <= len_a + len_b + len_c - 1:
            index = sequence[i] - len_a - len_b
            action_sequence.append(['fixed load', index])
        elif sequence[i] <= len_a + len_b + len_c + len_d - 1:
            index = sequence[i] - len_a - len_b - len_c
            action_sequence.append(['dispatch load', index])
        else:
            print('Error: sequence number %d exceeds total action count' % sequence[i])
            return

    return action_sequence
