import numpy as np


def verify_state_feasibility(ps):

    # Power factor flag
    pf_flag = 0
    for key, island in ps.islands.items():

        if key != 'blackout':
            load_ind = np.where(ps.octave.isload(island['gen']) == 1)[0]  # indicies of loads

            if len(load_ind) > 0:

                p_g = island['gen'][load_ind, 1]
                q_g = island['gen'][load_ind, 2]
                q_max = island['gen'][load_ind, 3]
                q_min = island['gen'][load_ind, 4]
                p_max = island['gen'][load_ind, 8]
                p_min = island['gen'][load_ind, 9]
                expected_pq = np.divide(p_max-p_min, q_max-q_min)
                actual_pq = np.divide(p_g, q_g)

                # Is power factor of dispatchable load consistent?
                if ~np.isclose(expected_pq, actual_pq, rtol=1e-13, atol=1e-13).any():
                    np.set_printoptions(precision=5)
                    print('\nExpected pf not achieved!')
                    print('island key: %s' % key)
                    print(~np.isclose(expected_pq, actual_pq, rtol=1e-20, atol=1e-20))
                    print('expected pq ratio: %s' % expected_pq)
                    print('actual pq ratio: %s' % actual_pq)
                    print('p: %s' % p_g)
                    print('q: %s\n' % q_g)
                    # Power factor of dispatchable loads not consistent!
                    pf_flag = 1

    if pf_flag == 1:
        return 0
    else:
        return 1

# Are generators consuming power?
# gen_ind = np.where(ps.octave.isload(island['gen']) == 0)[0]
# p_g = island['gen'][gen_ind, 1]
# if (p_g < 0).any():
#     print('\nGenerator consuming power!')
#     print(ps.octave.isload(island['gen']))
#     print('island key: %s' % key)
#     print('p: %s\n' % p_g)