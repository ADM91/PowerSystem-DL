from copy import deepcopy
from matplotlib import pyplot as plt
import numpy as np
import oct2py
from oct2py import octave
from set_opf_constraints import set_opf_constraints
from auxiliary.config import mp_opt


def make_iterable(obj):
    if type(obj) == list:
        return obj
    elif type(obj) == oct2py.io.Cell:
        return obj.reshape((-1,))
    else:
        return np.array([obj])


class PowerSystem(object):

    def __init__(self, ideal_case, n_deactivated):

        self.n_deactivated = n_deactivated

        # Set the opf constraints on the ideal case, before deconstruction
        self.ideal_case = set_opf_constraints(ideal_case)
        self.ideal_case = self.get_losses(self.ideal_case)
        self.ideal_case = self.is_load_is_gen(self.ideal_case)

        # Evaluate ideal state
        self.ideal_state = self.evaluate_state(self.ideal_case)

        # Deconstruct the ideal case
        self.broken_case = self.deactivate_branches()
        #
        # # Detect and isolate islands
        self.islands = self.get_islands(self.broken_case)
        self.islands_evaluated = self.evaluate_islands()

        self.current_state = self.evaluate_state(self.islands_evaluated)

        # Identify the broken state

    def initialize_state(self):

        gen_ind = (octave.isload(self.ideal_case['gen']) == 0).reshape((-1,))
        real_gen = self.ideal_case['gen'][gen_ind, :]
        real_gen = real_gen[:, [0, 1]]
        real_gen[:, 1] = np.nan

        d_load_ind = (octave.isload(self.ideal_case['gen']) == 1).reshape((-1,))
        dispatch_load = self.ideal_case['gen'][d_load_ind, :]  # Bus, active power
        dispatch_load = dispatch_load[:, [0, 1]]
        dispatch_load[:, 1] = np.nan

        f_load_ind = np.any(self.ideal_case['bus'][:, 2:4] > 0, axis=1)
        fixed_load = self.ideal_case['bus'][f_load_ind, :]
        fixed_load = fixed_load[:, [0, 2]]
        fixed_load[:, 1] = np.nan

        real_inj = self.ideal_case['branch'][:, [0, 1, 13]]
        real_inj[:, 2] = np.nan
        reactive_inj = self.ideal_case['branch'][:, [0, 1, 14]]
        reactive_inj[:, 2] = np.nan

        state = {'real gen': real_gen,
                 'dispatch load': dispatch_load,
                 'fixed load': fixed_load,
                 'real inj': real_inj,
                 'reactive inj': reactive_inj,
                 'losses': 0}

        return state

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
        for island in make_iterable(self.islands):

            # Only run for islands with both load and generation
            if island['is_gen'] and island['is_load']:
                result = octave.runopf(island, mp_opt)
                result = self.get_losses(result)
                opf_result.append(result)

            else:
                island['losses'] = 0
                opf_result.append(island)

        return opf_result

    @staticmethod
    def get_losses(case):

        # Evaluate system losses
        case['losses'] = np.real(np.sum(octave.get_losses(case['baseMVA'], case['bus'], case['branch'])))

        return case

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

    @staticmethod
    def is_load_is_gen(case_list):

        # Flag if there is gen and or load
        for island in make_iterable(case_list):

            # Does the island have loads?
            if np.all(island['bus'][:, 2:4] == 0) and np.all(octave.isload(island['gen']) == 0):  # True for no loads
                island['is_load'] = 0
            else:
                island['is_load'] = 1

            # Are there generators?
            if np.sum(octave.isload(island['gen']) == 0) > 0:
                island['is_gen'] = 1
            else:
                # If there are no generators, we can stop here
                island['is_gen'] = 0

        # Reshape case list if it is a oct2py cell
        if type(case_list) == oct2py.io.Cell:
            return case_list.reshape((-1))
        else:
            return case_list

    def get_islands(self, case):
        """
        Extracts islanded networks and places them in independent Matpower case structures
        """

        # Run the island detection function
        islands = octave.extract_islands(case)

        # Detect if there is load and or gen
        islands = self.is_load_is_gen(islands)

        for island in make_iterable(islands):

            # If there is both generation and loads
            if island['is_gen'] and island['is_load']:

                # Does island have reference bus?  Set ref as bus with highest unused capacity
                if not np.any(island['bus'][:, 1] == 3):  # True if reference bus is missing

                    # Find bus with largest unused capacity
                    largest = np.argmax(island['gen'][:, 8] - island['gen'][:, 1])
                    bus = island['gen'][largest, 0]

                    bus_index = island['bus'][:, 0] == bus

                    # Set bus as reference
                    island['bus'][bus_index, 1] = 3

                    island['slack_ind'] = np.where(island['bus'][:, 1] == 3)

        return islands

    def reconnect_islands(self):
        pass

    def reconnect_buses(self):
        pass

    def reconnect_load(self):
        pass

    def reconnect_gen(self):
        pass

    def evaluate_state(self, case_list):

        # Initialize the current state dictionary (has same elements as the ideal)
        current_state = self.initialize_state()

        # Loop through islands and collect info
        for island in make_iterable(case_list):

            # If there is both generation and load
            if island['is_gen'] and island['is_load']:

                # Fill in generator states for island i
                gen_ind = make_iterable(octave.isload(island['gen']) == 0).reshape((-1,))
                for bus_id in island['gen'][gen_ind, 0]:
                    ind1 = (current_state['real gen'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['gen'][gen_ind, 0] == bus_id).reshape((-1,))
                    current_state['real gen'][ind1, 1] = island['gen'][gen_ind, 1][ind2]

                # Fill in dispatchable load states for island i
                d_load_ind = make_iterable(octave.isload(island['gen']) == 1).reshape((-1,))
                for bus_id in island['gen'][d_load_ind, 0]:
                    ind1 = (current_state['dispatch load'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['gen'][d_load_ind, 0] == bus_id).reshape((-1,))
                    current_state['dispatch load'][ind1, 1] = island['gen'][d_load_ind, 1][ind2]

                # Fill fixed load states for island i
                f_load_ind = make_iterable(np.any(island['bus'][:, 2:4] > 0, axis=1)).reshape((-1,))
                for bus_id in island['bus'][f_load_ind, 0]:
                    ind1 = (current_state['fixed load'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['bus'][f_load_ind, 0] == bus_id).reshape((-1,))
                    current_state['fixed load'][ind1, 1] = island['bus'][f_load_ind, 2][ind2]

                # Fill real injection to each line for island i
                for from_to in island['branch'][:, [0, 1, 13, 14]]:
                    # print(from_to)
                    ind1 = np.all(current_state['real inj'][:, 0:2] == from_to[0:2], axis=1)
                    current_state['real inj'][ind1, 2] = from_to[2]
                    current_state['reactive inj'][ind1, 2] = from_to[3]

            # If either generation or load is missing
            else:
                # Fill in generator states for island i
                gen_ind = make_iterable(octave.isload(island['gen']) == 0).reshape((-1,))
                for bus_id in island['gen'][gen_ind, 0]:
                    ind1 = (current_state['real gen'][:, 0] == bus_id).reshape((-1,))
                    current_state['real gen'][ind1, 1] = 0

                # Fill in dispatchable load states for island i
                d_load_ind = make_iterable(octave.isload(island['gen']) == 1).reshape((-1,))
                for bus_id in island['gen'][d_load_ind, 0]:
                    ind1 = (current_state['dispatch load'][:, 0] == bus_id).reshape((-1,))
                    current_state['dispatch load'][ind1, 1] = 0

                # Fill fixed load states for island i
                f_load_ind = make_iterable(np.any(island['bus'][:, 2:4] > 0, axis=1)).reshape((-1,))
                for bus_id in island['bus'][f_load_ind, 0]:
                    ind1 = (current_state['fixed load'][:, 0] == bus_id).reshape((-1,))
                    current_state['fixed load'][ind1, 1] = 0

                # Fill real injection to each line for island i
                for from_to in island['branch'][:, [0, 1, 13, 14]]:
                    ind1 = np.all(current_state['real inj'][:, 0:2] == from_to[0:2], axis=1)
                    current_state['real inj'][ind1, 2] = 0
                    current_state['reactive inj'][ind1, 2] = 0

            # Aggregate losses
            current_state['losses'] += island['losses']

        return current_state

    def visualize_state(self):

        # Initialize figure
        plt.figure(1, figsize=(12, 12))

        # Prep generator data
        gen_max = self.ideal_case['gen'][(octave.isload(self.ideal_case['gen']) == 0).reshape((-1)), 8].reshape((-1,))
        gen_ideal = self.ideal_state['real gen'][:, 1].reshape((-1,))
        gen_current = self.current_state['real gen'][:, 1].reshape((-1,))
        gen_bus = self.ideal_state['real gen'][:, 0].reshape((-1,))
        cap_order = np.argsort(gen_max, axis=0, kind='quicksort')
        width = 0.25
        x = np.arange(gen_max.shape[0])

        # Plot generator data
        ax1 = plt.subplot2grid((3, 2), (0, 0))
        ax1.bar(x, gen_max[cap_order], width*2, align='center', alpha=0.3, color='blue')
        ax1.bar(x-width/2, gen_ideal[cap_order], width, align='center', alpha=0.9, color='green')
        ax1.bar(x+width/2, gen_current[cap_order], width, align='center', alpha=0.9, color='red')
        ax1.set_xticks(x)
        ax1.set_xticklabels(['bus %d' % i for i in gen_bus[cap_order]])
        plt.title('Generator schedule')
        ax1.legend(['Gen limit', 'Ideal state', 'Current state'], loc='upper left')
        ax1.set_ylabel('Power (MW)')

        # Prep dispatchable load data
        # d_load_max = self.ideal_case['gen'][(octave.isload(self.ideal_case['gen']) == 1).reshape((-1)), 8].reshape((-1,))
        d_load_ideal = -self.ideal_state['dispatch load'][:, 1].reshape((-1,))
        d_load_current = -self.current_state['dispatch load'][:, 1].reshape((-1,))
        d_load_bus = self.ideal_state['dispatch load'][:, 0].reshape((-1,))
        d_load_order = np.argsort(d_load_ideal, axis=0, kind='quicksort')
        width = 0.35
        x = np.arange(d_load_ideal.shape[0])

        # Plot dispatchable load data
        ax2 = plt.subplot2grid((3, 2), (0, 1))
        ax2.bar(x, d_load_ideal[d_load_order], width, align='center', alpha=0.3, color='green')
        ax2.bar(x, d_load_current[d_load_order], width, align='center', alpha=0.9, color='red')
        ax2.set_xticks(x)
        ax2.set_xticklabels(['bus %d' % i for i in d_load_bus[d_load_order]])
        plt.title('Dispatchable loads')
        ax2.legend(['Ideal load', 'Current load'], loc='upper left')
        ax2.set_ylabel('Power (MW)')




