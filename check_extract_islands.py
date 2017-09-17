from oct2py import octave
import numpy as np
# import collections


# def get_iterable(x):
#     if isinstance(x, collections.Iterable):
#         return x
#     else:
#         return (x,)


def check_extract_islands(base_case_contingency):

    # Run the island detection function
    islands = octave.extract_islands(base_case_contingency)
    # islands.shape
    # islands = get_iterable(islands)

    if islands.shape == (1,):
        islands = islands.reshape((1, 1))

    # islands.shape

    # If multiple islands exist, do stuff
    for i, isl in enumerate(islands[0]):

        # TODO: Calculate generation load mismatch?

        # Does the island have no loads?
        if np.all(isl['bus'][:, 2:4] == 0):  # True for no loads
            isl['is_load'] = 0
        else:
            isl['is_load'] = 1

        # Are there generators?
        if len(isl['gen']) > 0:
            isl['is_gen'] = 1
        else:
            # If there are no generators, we can stop here
            isl['is_gen'] = 0
            continue

        # Does island have reference bus?  Set ref as bus with highest unused capacity
        if not np.any(isl['bus'][:, 1] == 3):  # True if reference bus is missing

            # Find bus with largest unused capacity
            largest = np.argmax(isl['gen'][:, 8] - isl['gen'][:, 1])
            bus = isl['gen'][largest, 0]

            bus_index = isl['bus'][:, 0] == bus

            # Set bus as reference
            isl['bus'][bus_index, 1] = 3

        isl['slack_ind'] = np.where(isl['bus'][:, 1] == 3)

    return islands[0]
