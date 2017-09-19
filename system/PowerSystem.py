from copy import deepcopy
import numpy as np
from oct2py import octave
from set_opf_constraints import set_opf_constraints
from auxiliary.config import mp_opt


class PowerSystem(object):

    def __init__(self, ideal_case, n_deactivated):

        # Set the opf constraints on the ideal case, before deconstruction
        # self.ideal_case = octave.runpf(ideal_case, mp_opt)
        self.ideal_case = set_opf_constraints(ideal_case)


        self.ideal_state = {'real gen': ideal_case['gen'][disp_load == 0, [0, 1]],
                            'real load': ideal_case['bus'][:, [0, 2]],
                            'real inj': ideal_case['branch'][:, [0, 1, 13]],
                            'reactive inj': ideal_case['branch'][:, [0, 1, 14]],
                            'losses': None}

        self.n_deactivated = n_deactivated


        # self.broken_case = self.deactivate_branches()
        # self.islands = self.get_islands()
        #
        # self.islands_constrained = self.constrain_islands()
        # self.islands_evaluated = self.evaluate_islands()
        # self.current_state = self.evaluate_state()


        # Identify the broken state
    def initialize_state(self):

        # TODO: this is where i left off

        disp_load = octave.isload(self.ideal_case['gen'])
        fixed_load = np.any(self.ideal_case['bus'][:, 2:4] > 0, axis=1)


        gen = np.hstack((self.ideal_case['gen'][disp_load == 0, 0], self.ideal_case['gen'][disp_load == 0, 0])
        load = np.vstack(self.ideal_case['gen'][disp_load == 1, 0], self.ideal_case['bus'][fixed_load, 0]))



        state = {'real gen': gen,
                            'real load': ideal_case['bus'][:, [0, 2]],
                            'real inj': ideal_case['branch'][:, [0, 1, 13]],
                            'reactive inj': ideal_case['branch'][:, [0, 1, 14]],
                            'losses': None}

    def constrain_islands(self):

        # Loop through the islands
        constrained = list()
        for i, island in enumerate(self.islands):
            # Set constraints
            island_constrained = set_opf_constraints(island, set_gen=True, set_loads=True)
            island_constrained['opf ran'] = 1

            if not island['is_gen'] or not island['is_load']:
                print('THERE IS A BLACKOUT HERE')
                island_constrained['gen'][:, 7] = 0  # status of gen and loads= off
                island_constrained['opf ran'] = 0

            # Run opf on island
            constrained.append(island_constrained)

        return constrained

    def evaluate_islands(self):

        # Loop through the islands
        opf_result = list()
        for i, island in enumerate(self.islands_constrained):

            # Only run for islands with both load and generation
            if island['is_gen'] and island['is_load']:
                result = octave.runopf(island, mp_opt)
                result['losses'] = np.real(np.sum(octave.get_losses(result['baseMVA'], result['bus'], result['branch'])))
                opf_result.append(result)

            else:
                island['losses'] = np.array(0)
                opf_result.append(island)



        return opf_result

    def deactivate_branches(self):
        """
        Removes random lines from the system.
        """

        # Number of branches
        n = self.ideal_case['branch'].shape[0]

        # select random integers in range 0 : n-1
        remove = np.random.choice(n, size=self.n_deactivated, replace=False)

        # Create copy of case
        new_case = deepcopy(self.ideal_case)

        # Remove the line(s) from copy
        new_case['branch'][remove, 10] = 0

        new_case['disconnected'] = remove

        return new_case

    def get_islands(self):
        """
        Extracts islanded networks and places them in independent Matpower case structures
        """

        # Run the island detection function
        islands = octave.extract_islands(self.broken_case)

        # Reshape if only one island exists
        if islands.shape == (1,):
            islands = islands.reshape((1, 1))

        # If multiple islands exist, do stuff
        for i, isl in enumerate(islands[0]):

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

    def reconnect_islands(self):
        pass

    def reconnect_buses(self):
        pass

    def reconnect_load(self):
        pass

    def reconnect_gen(self):
        pass

    def evaluate_state(self):

        # Initialize the current state dictionary (has same elements as the ideal)
        current_state = {'real gen': np.full_like(self.ideal_state['real gen'], np.nan),
                         'real load': np.full_like(self.ideal_state['real load'], np.nan),
                         'real inj': np.full_like(self.ideal_state['real inj'], np.nan),
                         'reactive inj': np.full_like(self.ideal_state['reactive inj'], np.nan),
                         'losses': np.nan}

        # Loop through islands and collect info
        for i, island in enumerate(self.islands_evaluated):

            print(island['branch'][:, 0:2] == self.ideal_state['real inj'][:, 0:2])

            if island['is_gen'] and island['is_load']:

                # Get relevant matrix indices
                ind1 = island['gen'][:, 0] == self.ideal_state['real gen'][:, 0]
                ind2 = island['bus'][:, 0] == self.ideal_state['real load'][:, 0]
                ind3 = np.all(island['branch'][:, 0:2] == self.ideal_state['real inj'][:, 0:2], axis=1)


                current_state['real gen'][ind1, :] = island['gen'][:, [0, 1]]
                current_state['real load'][ind2, :] = island['bus'][:, [0, 2]]
                current_state['real inj'][ind3, :] = island['bus'][:, [0, 1, 13]]
                current_state['reactive inj'][ind3, :] = island['bus'][:, [0, 1, 14]]
            else:
                pass

        current_state['losses'] += island['losses']

        return current_state

    def visualize_state(self):
        pass







