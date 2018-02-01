import numpy as np


def selection(n_pairs, cost):

    # Select best out of two random individuals
    n = len(cost)
    pairs = np.empty((n_pairs, 2), dtype='l')
    for i in range(n_pairs):
        for ii in range(2):
            s1 = int(np.random.choice(n))
            s2 = int(np.random.choice(n))

            if cost[s1] < cost[s2]:
                pairs[i, ii] = s1
                # print('selected %s out of %s %s' % (cost[s1], cost[s1], cost[s2]))
            else:
                pairs[i, ii] = s2
                # print('selected %s out of %s %s' % (cost[s2], cost[s1], cost[s2]))

    return pairs

