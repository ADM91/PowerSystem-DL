import numpy as np
from copy import copy


def mutate(children, eta):

    n, m = children.shape

    print('prior to mutation')
    print(children)

    for i in range(n):
        r = np.random.rand()
        if r < eta:
            # child[[s1, s2]] = child[[s2, s1]]

            # Slide method
            child = children[i, :]
            # print('\noriginal: %s' % child)
            s1 = int(np.random.choice(m))
            s2 = int(np.random.choice(m))
            s = np.sort([s1, s2])
            slice_1 = child[:s[0]]
            slice_2 = child[s[0]:s[1]]
            slice_3 = child[s[1]:]

            # if s1 < s2:
            #     children[i, :] = np.hstack((slice_1, slice_2[1:], slice_3[0], slice_2[0], slice_3[1:]))
            # else:
            children[i, :] = np.hstack((slice_1, slice_3[0], slice_2, slice_3[1:]))

            # print('mutated : %s' % child)
            # print('s1: %s\ns2: %s\n' % (s1, s2))
    print('after mutation')
    print(children)

    return children

