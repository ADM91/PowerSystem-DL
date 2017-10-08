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

        # # Detect and isolate islands, identify blackout zone
        # self.islands = self.get_islands(self.broken_case)
        self.islands = dict()
        self.get_islands(self.broken_case)

        # Identify any missing elements after islanding - requires comparison of islands to ideal case - similar to evaluate state function!!!


        # Islands evalutated
        # self.islands_evaluated = list()
        # self.evaluate_islands()
        #
        # # Get current state
        # self.current_state = self.evaluate_state(self.islands_evaluated)
        #
        # # Identify the disconnected system elements - uses the current state variable and islands
        # self.disconnected_elements = self.id_disconnected_elements()

    def convert_to_mpc(self):
        # Converts the evaluated islands back to a matpower case so it can be ran again
        count = 0
        for island in make_iterable(self.islands_evaluated):
            obj = octave.opf_model(island)
            self.islands[count] = octave.get_mpc(obj)
            count += 1

    def id_disconnected_elements(self):

        # Initialize disconnected elements dictionary
        elements = {'lines': [],
                    'fixed loads': [],
                    'generators': []}

        # Line is disconnected if it appears as nan in current state or is marked as status 0 in islands
        for island in make_iterable(self.islands_evaluated):
            branch_id = (island['branch'][:, 10] == 0).reshape((-1))
            elements['lines'] = np.append(elements['lines'], island['branch'][branch_id, 0:2]).reshape((-1, 2))

        # Add nans to the list, they do not belong to any island
        branch_id = np.isnan(self.current_state['real inj'][:, 2]).reshape((-1,))
        elements['lines'] = np.append(elements['lines'], self.current_state['real inj'][branch_id, 0:2]).reshape((-1, 2))

        # The missing fixed loads will be nan in current state
        bus_id = np.isnan(self.current_state['fixed load'][:, 1]).reshape((-1,))
        elements['fixed loads'] = self.current_state['fixed load'][bus_id, 0].reshape((-1, 1))

        # Or they could be equal to zero
        bus_id = (self.current_state['fixed load'][:, 1] == 0).reshape((-1,))
        elements['fixed loads'] = np.append(elements['fixed loads'], self.current_state['fixed load'][bus_id, 0].reshape((-1, 1)))

        # The off-line generators will also appear as nan
        bus_id = np.isnan(self.current_state['real gen'][:, 1]).reshape((-1,))
        elements['generators'] = self.current_state['real gen'][bus_id, 0].reshape((-1, 1))

        return elements

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

        bus_voltage_ang = self.ideal_case['bus'][:, [0,8]]
        bus_voltage_ang[:, 1] = np.nan

        state = {'real gen': real_gen,
                 'dispatch load': dispatch_load,
                 'fixed load': fixed_load,
                 'real inj': real_inj,
                 'reactive inj': reactive_inj,
                 'bus voltage angle': bus_voltage_ang,
                 'losses': 0}

        return state

    def evaluate_islands(self):

        # Important note: When runopf is executed, the gencost matrix is destroyed. To remedy this, I save the matrix
        # and overwrite the result with this prior gencost matrix

        # Loop through the islands
        self.islands_evaluated = list()  # Re-initialize (we need to evaluate islands between actions)
        for island in make_iterable(self.islands):

            # Only run for islands with both load and generation
            if island['is_gen'] and island['is_load']:
                gencost = deepcopy(island['gencost'])
                result = octave.runopf(island, mp_opt)
                result = self.get_losses(result)
                result['gencost'] = gencost
                self.islands_evaluated.append(result)

            else:
                island['losses'] = 0
                self.islands_evaluated.append(island)

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

    def get_islands(self, case):
        """
        Extracts islanded networks and places them in independent Matpower case structures
        """

        # Run the island detection function
        islands = octave.extract_islands(case)

        # Detect if there is load and or gen
        islands = self.is_load_is_gen(islands)

        # Initialize blackout dictionary to empty arrays
        self.islands['blackout'] = {'bus': np.empty((0, self.ideal_case['bus'].shape[1])),
                                    'branch': np.empty((0, self.ideal_case['branch'].shape[1])),
                                    'gen': np.empty((0, self.ideal_case['gen'].shape[1])),
                                    'gencost': np.empty((0, self.ideal_case['gencost'].shape[1])),
                                    'connections': list(),
                                    'is_load': 0,
                                    'is_gen': 0,
                                    'losses': 0}
        count = 0
        for island in make_iterable(islands):

            # If there is both generation and loads
            if island['is_gen'] and island['is_load']:
                print('gen: %s\nload: %s' % (island['is_gen'], island['is_load']))

                # Does island have a reference bus?  Set ref as bus with highest unused capacity
                if not np.any(island['bus'][:, 1] == 3):  # True if reference bus is missing

                    # Find bus with largest unused capacity
                    largest = np.argmax(island['gen'][:, 8] - island['gen'][:, 1])
                    bus = island['gen'][largest, 0]

                    bus_index = island['bus'][:, 0] == bus

                    # Set bus as reference
                    island['bus'][bus_index, 1] = 3

                    island['slack_ind'] = np.where(island['bus'][:, 1] == 3)

                # Add energized island to the islands dictionary
                self.islands['%s' % count] = island

                count += 1

            else:  # Gen or loads missing: blackout islands
                print('gen: %s\nload: %s' % (island['is_gen'], island['is_load']))

                # Deconstruct island and place its elements in blackout zone
                self.islands['blackout']['bus'] = np.append(self.islands['blackout']['bus'],
                                                            island['bus'], axis=0)
                self.islands['blackout']['branch'] = np.append(self.islands['blackout']['branch'],
                                                               island['branch'], axis=0)
                self.islands['blackout']['gen'] = np.append(self.islands['blackout']['gen'],
                                                            island['gen'], axis=0)
                self.islands['blackout']['gencost'] = np.append(self.islands['blackout']['gencost'],
                                                                island['gencost'], axis=0)

        # Add left over blackout elements! We need to evaluate the state and check for nans
        state = self.evaluate_state(list(self.islands.values()))

        # Populate blackout buses
        bus_ind = np.isnan(state['bus voltage angle'][:, 1]).reshape((-1,))
        bus_id = state['bus voltage angle'][bus_ind, 0]
        for b_id in bus_id:
            ind1 = (self.ideal_case['bus'][:, 0] == b_id).reshape((-1,))
            self.islands['blackout']['bus'] = np.append(self.islands['blackout']['bus'],
                                                        self.ideal_case['bus'][ind1, :], axis=0)
        # Populate blackout branches
        branch_ind = np.isnan(state['real inj'][:, 2]).reshape((-1,))
        branch_id = state['real inj'][branch_ind, 0:2]
        for from_to in branch_id:
            ind1 = np.all(self.ideal_case['branch'][:, 0:2] == from_to, axis=1).reshape((-1,))
            self.islands['blackout']['branch'] = np.append(self.islands['blackout']['branch'],
                                                           self.ideal_case['branch'][ind1, :], axis=0)

        # Populate blackout generators
        gen_ind = np.isnan(state['real gen'][:, 1]).reshape((-1,))
        gen_id = state['real gen'][gen_ind, 0]
        for g_id in gen_id:
            ind1 = (self.ideal_case['gen'][:, 0] == g_id).reshape((-1,))
            self.islands['blackout']['gen'] = np.append(self.islands['blackout']['gen'],
                                                        self.ideal_case['gen'][ind1, :], axis=0)
            self.islands['blackout']['gencost'] = np.append(self.islands['blackout']['gencost'],
                                                            self.ideal_case['gencost'][ind1, :], axis=0)

    def evaluate_state(self, island_list):

        # Initialize the current state dictionary (has same elements as the ideal)
        state = self.initialize_state()

        # Loop through islands and collect info
        for island in make_iterable(island_list):

            # If there is both generation and load
            if island['is_gen'] and island['is_load']:

                print('There is gen and load, Im going to the opf output to pull data')

                # Fill in generator states for island i
                gen_ind = make_iterable(octave.isload(island['gen']) == 0).reshape((-1,))
                for bus_id in island['gen'][gen_ind, 0]:
                    ind1 = (state['real gen'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['gen'][gen_ind, 0] == bus_id).reshape((-1,))
                    state['real gen'][ind1, 1] = island['gen'][gen_ind, 1][ind2]

                # Fill in dispatchable load states for island i
                d_load_ind = make_iterable(octave.isload(island['gen']) == 1).reshape((-1,))
                for bus_id in island['gen'][d_load_ind, 0]:
                    ind1 = (state['dispatch load'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['gen'][d_load_ind, 0] == bus_id).reshape((-1,))
                    state['dispatch load'][ind1, 1] = island['gen'][d_load_ind, 1][ind2]

                # Fill fixed load states for island i
                f_load_ind = make_iterable(np.any(island['bus'][:, 2:4] > 0, axis=1)).reshape((-1,))
                for bus_id in island['bus'][f_load_ind, 0]:
                    ind1 = (state['fixed load'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['bus'][f_load_ind, 0] == bus_id).reshape((-1,))
                    state['fixed load'][ind1, 1] = island['bus'][f_load_ind, 2][ind2]

                # Fill real injection to each line for island i
                for from_to in island['branch'][:, [0, 1, 13, 14]]:
                    # print(from_to)
                    ind1 = np.all(state['real inj'][:, 0:2] == from_to[0:2], axis=1)
                    state['real inj'][ind1, 2] = from_to[2]
                    state['reactive inj'][ind1, 2] = from_to[3]

                # Fill bus voltage angle for island i
                for bus_id in island['bus'][:, 0]:
                    ind1 = (state['bus voltage angle'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['bus'][:, 0] == bus_id).reshape((-1,))
                    state['bus voltage angle'][ind1, 1] = island['bus'][ind2, 8]

            # If either generation or load is missing
            else:

                print('Blackout area :(')

                # Fill in generator states for island i
                if len(island['gen']) > 0:
                    gen_ind = make_iterable(octave.isload(island['gen']) == 0).reshape((-1,))
                    for bus_id in island['gen'][gen_ind, 0]:
                        ind1 = (state['real gen'][:, 0] == bus_id).reshape((-1,))
                        state['real gen'][ind1, 1] = 0

                    # Fill in dispatchable load states for island i
                    d_load_ind = make_iterable(octave.isload(island['gen']) == 1).reshape((-1,))
                    for bus_id in island['gen'][d_load_ind, 0]:
                        ind1 = (state['dispatch load'][:, 0] == bus_id).reshape((-1,))
                        state['dispatch load'][ind1, 1] = 0

                # Fill fixed load states for island i
                if len(island['bus']) > 0:
                    f_load_ind = make_iterable(np.any(island['bus'][:, 2:4] > 0, axis=1)).reshape((-1,))
                    for bus_id in island['bus'][f_load_ind, 0]:
                        ind1 = (state['fixed load'][:, 0] == bus_id).reshape((-1,))
                        state['fixed load'][ind1, 1] = 0

                    # Fill bus voltage angle for island i
                    for bus_id in island['bus'][:, 0]:
                        ind1 = (state['bus voltage angle'][:, 0] == bus_id).reshape((-1,))
                        state['bus voltage angle'][ind1, 1] = 0

                # Fill real injection to each line for island i
                if len(island['branch']) > 0:
                    for from_to in island['branch'][:, [0, 1, 13, 14]]:
                        ind1 = np.all(state['real inj'][:, 0:2] == from_to[0:2], axis=1)
                        state['real inj'][ind1, 2] = 0
                        state['reactive inj'][ind1, 2] = 0



            # Aggregate losses
            state['losses'] += island['losses']

        return state

    def visualize_state(self, fig_num=1):

        # Initialize figure
        plt.figure(fig_num, figsize=(12, 12))

        # Prep generator data
        gen_max = self.ideal_case['gen'][(octave.isload(self.ideal_case['gen']) == 0).reshape((-1)), 8].reshape((-1,))
        gen_ideal = self.ideal_state['real gen'][:, 1].reshape((-1,))
        gen_current = self.current_state['real gen'][:, 1].reshape((-1,))
        gen_bus = self.ideal_state['real gen'][:, 0].reshape((-1,))
        cap_order = np.argsort(gen_max, axis=0, kind='quicksort')
        width = 0.25
        x = np.arange(len(gen_max))

        # Plot generator data
        ax1 = plt.subplot2grid((2, 2), (0, 0))
        ax1.bar(x, gen_max[cap_order], width*2, align='center', alpha=0.3, color='green')
        ax1.bar(x-width/2, gen_ideal[cap_order], width, align='center', alpha=0.9, color='blue')
        ax1.bar(x+width/2, gen_current[cap_order], width, align='center', alpha=0.9, color='red')
        ax1.set_xticks(x)
        ax1.set_xticklabels(['bus %d' % i for i in gen_bus[cap_order]])
        plt.title('Generator schedule')
        ax1.legend(['Generator limit', 'Ideal state', 'Current state'], loc='upper left')
        ax1.set_ylabel('Power (MW)')

        # Prep dispatchable load data
        d_load_ideal = -self.ideal_state['dispatch load'][:, 1].reshape((-1,))
        d_load_current = -self.current_state['dispatch load'][:, 1].reshape((-1,))
        d_load_bus = self.ideal_state['dispatch load'][:, 0].reshape((-1,))
        d_load_order = np.argsort(d_load_ideal, axis=0, kind='quicksort')
        width = 0.5
        x1 = np.arange(len(d_load_ideal))

        # Prep fixed load data
        f_load_ideal = self.ideal_state['fixed load'][:, 1].reshape((-1,))
        f_load_current = self.current_state['fixed load'][:, 1].reshape((-1,))
        f_load_bus = self.ideal_state['fixed load'][:, 0].reshape((-1,))
        f_load_order = np.argsort(f_load_ideal, axis=0, kind='quicksort')
        x2 = np.arange(len(x1) + 1, len(x1) + 1 + len(f_load_ideal))

        # Plot load data
        ax2 = plt.subplot2grid((2, 2), (0, 1))
        ax2.bar(x1, d_load_ideal[d_load_order], width, align='center', alpha=0.3, color='blue')
        ax2.bar(x1, d_load_current[d_load_order], width, align='center', alpha=0.9, color='red')
        ax2.bar(x2, f_load_ideal[f_load_order], width, align='center', alpha=0.3, color='blue')
        ax2.bar(x2, f_load_current[f_load_order], width, align='center', alpha=0.9, color='red')
        ax2.set_xticks(np.concatenate((x1, x2)))
        ticks = np.concatenate((['b %d' % i for i in d_load_bus[d_load_order]], ['b %d' % i for i in f_load_bus[f_load_order]]))
        ax2.set_xticklabels(ticks)
        plt.title('Load Profile')
        ax2.legend(['Ideal load', 'Current load'], loc='upper left')
        ax2.set_ylabel('Power (MW)')

        # Prep line loadings data
        mva_rating = self.ideal_case['branch'][:, 5].reshape((-1,))
        real_inj_ideal = np.abs(self.ideal_state['real inj'][:, 2].reshape((-1,)))
        real_inj_current = np.abs(self.current_state['real inj'][:, 2].reshape((-1,)))
        real_inj_buses = np.abs(self.ideal_state['real inj'][:, 0:2].reshape((-1, 2)))
        line_order = np.argsort(mva_rating, axis=0, kind='quicksort')
        width = 0.25
        x = np.arange(len(mva_rating))

        # Plot line data
        ax3 = plt.subplot2grid((2, 2), (1, 0), colspan=2)
        ax3.bar(x, mva_rating[line_order], width*2, align='center', alpha=0.3, color='green')
        ax3.bar(x-width/2, real_inj_ideal[line_order], width, align='center', alpha=0.9, color='blue')
        ax3.bar(x+width/2, real_inj_current[line_order], width, align='center', alpha=0.9, color='red')
        ax3.set_xticks(x)
        ticks = ['%d - %d' % (i[0], i[1]) for i in real_inj_buses[line_order]]
        ax3.set_xticklabels(ticks)
        plt.title('Line loadings')
        ax3.legend(['Line limit', 'Ideal load', 'Current load'], loc='upper left')
        ax3.set_ylabel('Power (MW)')
        plt.xlim([-1, len(line_order)])

        plt.tight_layout()
        plt.show()
        plt.draw()

    def action_line(self, bus_ids):
        """Line connection case list:

        1. Line within an energized island is enabled
            * Very common, simplest
            * Easy to impplement, just switch on
        2. Line between 2 energized islands is enabled
            * Bit more complex than within island case
            * Need to consolidate the islands into one
            * Need to remove one of the slack buses
        3. Line between an energized island and "left overs" is enabled
            * Consult the connection list to see if there are further connections there
            * Add the "left over" bus(s) to the island
            * Add the "left over" branch(s) to the island and enable
            * Add any generation or dispatchable load to the island, but don't enable, this occurs as separate action
            * If there is new fixed load, disable it, enabling it is a separate action
        4. Line within "left overs" is enabled
            * I need to implement a connection list to monitor what has been connected
            * These buses will be connected and added to the connection list


        """

        print('Connected lines')
        for island in make_iterable(self.islands):
            print(island['branch'][:, 10])
        print('\n')

        print('bus ids')
        print(bus_ids)
        print('\n')

        # Check islands to find bus 1
        island_1 = None
        for i, island in enumerate(make_iterable(self.islands)):
            if np.any(island['bus'][:, 0] == bus_ids[0]):
                island_1 = i
        print('island 1: %s\n' % island_1)

        # Check islands to find bus 2
        island_2 = None
        for i, island in enumerate(make_iterable(self.islands)):
            if np.any(island['bus'][:, 0] == bus_ids[1]):
                island_2 = i
        print('island 2: %s\n' % island_2)

        # If islands are same, its simple
        # TODO: Need to identify all corner cases (ex. can you have a line with two None buses?)
        if island_1 == island_2 and island_1 is not None:
            print('Line does not connect islands\n')
            ind = np.all(self.islands[island_1]['branch'][:, 0:2] == bus_ids, axis=1)
            # print(self.islands[island_1]['branch'][:, 0:2])
            # print(self.islands[island_1]['branch'][:, 0:2] == bus_ids)
            # print(ind)
            # print('\n')

            # Need to set opf contraints and run opf
            self.islands[island_1]['branch'][ind, 10] = 1  # Change branch status to 1 (in-service)

            # Show reconection of line
            print('Connected lines')
            for island in make_iterable(self.islands):
                print(island['branch'][:, 10])

        # In these cases, add the line and energize/enable the line to the island
        # Turns out that in these cases, energizing a line with nothing on the None end, convergence failure occurs!!
        # Convergence failure occured when connecting line 1-2, which is typically a very high load line...
        # Current method worked fine on smaller lines.
        # How do I fix this? Add a load or gen at the new bus?
        elif island_1 is None and island_2 is not None:
            print('Line connects to None\n')
            # Add the missing bus (bus 1) from ideal case
            ind = self.ideal_case['bus'][:, 0] == bus_ids[0]
            print(ind)
            self.islands[island_2]['bus'] = np.append(self.islands[island_2]['bus'],
                                                      self.ideal_case['bus'][ind, :], axis=0)

            # Add the missing branch from ideal case
            ind = np.all(self.ideal_case['branch'][:, 0:2] == bus_ids, axis=1)
            print(ind)
            self.islands[island_2]['branch'] = np.append(self.islands[island_2]['branch'],
                                                         self.ideal_case['branch'][ind, :], axis=0)

        elif island_2 is None and island_1 is not None:
            print('Line connects to None\n')
            # Add the missing bus (bus 2) from ideal case
            ind = self.ideal_case['bus'][:, 0] == bus_ids[1]
            print(ind)
            self.islands[island_1]['bus'] = np.append(self.islands[island_1]['bus'],
                                                      self.ideal_case['bus'][ind, :], axis=0)

            # Add the missing branch from ideal case
            ind = np.all(self.ideal_case['branch'][:, 0:2] == bus_ids, axis=1)
            print(ind)
            self.islands[island_1]['branch'] = np.append(self.islands[island_1]['branch'],
                                                         self.ideal_case['branch'][ind, :], axis=0)

        # If islands differ, we have to combine their case structures!
        # TODO: this needs debugging
        else:
            print('Connecting islands %s and %s \n' % (island_1, island_2))

            # Append all of island 2 to island 1
            # self.islands[island_1] = deepcopy(self.islands[island_1])
            self.islands[island_1]['bus'] = np.append(self.islands[island_1]['bus'], self.islands[island_2]['bus'], axis=0)
            self.islands[island_1]['branch'] = np.append(self.islands[island_1]['branch'], self.islands[island_2]['branch'], axis=0)
            self.islands[island_1]['gen'] = np.append(self.islands[island_1]['gen'], self.islands[island_2]['gen'], axis=0)
            self.islands[island_1]['gencost'] = np.append(self.islands[island_1]['gencost'], self.islands[island_2]['gencost'], axis=0)

            # Delete island 2
            self.islands = np.delete(self.islands, island_2)

            # Remember: to remove the weaker of the swing buses!
            # ind = self.islands[island_1]['bus'][:, 1] == 3
            # print(ind)
            # bus_id = self.islands[island_1]['bus'][ind, 0]
            # print(bus_id)
            # gen_ind = self.islands[island_1]['gen'][:, 0] == bus_id
            # print(gen_ind)
            # gen_cap = self.islands[island_1]['gen'][gen_ind, 8]
            # print(gen_cap)
            # gen_weak_ind = self.islands[island_1]['gen'][:, 8] == np.min(gen_cap)
            # print(gen_weak_ind)
            # gen_weak_bus_id = self.islands[island_1]['gen'][gen_weak_ind, 0]
            # print(gen_weak_bus_id)
            # weak_bus_ind = self.islands[island_1]['bus'][:, 0] == gen_weak_bus_id
            # print(weak_bus_ind)
            #
            # # Set weak bus type to 1 (PQ bus)
            # self.islands[island_1]['bus'][weak_bus_ind, 1] = 1

        # Update disconnected element dictionary
        ind = np.all(self.disconnected_elements['lines'][:, 0:2] == bus_ids, axis=1)
        self.disconnected_elements['lines'] = np.delete(self.disconnected_elements['lines'], np.where(ind), 0)

    def action_load(self, bus_id):
        pass

    def action_gen(self, bus_id):
        pass

    @staticmethod
    def get_losses(case):

        # Evaluate system losses
        case['losses'] = np.real(np.sum(octave.get_losses(case['baseMVA'], case['bus'], case['branch'])))

        return case

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

    # def constrain_islands(self):
    #
    #     # Loop through the islands
    #     constrained = list()
    #     for i, island in enumerate(self.islands):
    #         # Set constraints
    #         island_constrained = set_opf_constraints(island, set_gen=True, set_loads=True)
    #         island_constrained['opf ran'] = 1
    #
    #         if not island['is_gen'] or not island['is_load']:
    #             print('THERE IS A BLACKOUT HERE')
    #             island_constrained['gen'][:, 7] = 0  # status of gen and loads= off
    #             island_constrained['opf ran'] = 0
    #
    #         # Run opf on island
    #         constrained.append(island_constrained)
    #
    #     return constrained