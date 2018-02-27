from copy import deepcopy
import numpy as np


def power_deviation(states, ideal_state):

    ideal_losses = deepcopy(ideal_state['losses'])
    ideal_gen = deepcopy(ideal_state['real gen'][:, 1])
    ideal_fixed = deepcopy(ideal_state['fixed load'][:, 1])
    ideal_dispatched = deepcopy(ideal_state['dispatch load'][:, 1])

    gen_dev = []
    load_dev = []
    loss_dev = []

    for state in states:

        gen_dev.append(np.sum(np.abs(ideal_gen - state['real gen'][:, 1])))
        f = np.sum(np.abs(ideal_fixed - state['fixed load'][:, 1]))
        d = np.sum(np.abs(ideal_dispatched - state['dispatch load'][:, 1]))
        # print(np.abs(ideal_fixed - state['fixed load'][:, 1]))
        # print(np.abs(ideal_dispatched - state['dispatch load'][:, 1]))
        # print('\n')
        load_dev.append(np.sum([f, d]))
        loss_dev.append(-(ideal_losses - state['losses']))

    return [gen_dev, load_dev, loss_dev]
