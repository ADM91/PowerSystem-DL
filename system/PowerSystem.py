from copy import deepcopy
import time
from pprint import PrettyPrinter
from matplotlib import pyplot as plt
import matplotlib.animation as animation
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

    def __init__(self, ideal_case, n_deactivated, verbose=1):

        self.pp = PrettyPrinter(indent=4)

        self.n_deactivated = n_deactivated
        self.verbose = verbose

        # Set the opf constraints on the ideal case, before deconstruction
        self.ideal_case = set_opf_constraints(ideal_case)
        self.ideal_case = self.get_losses(self.ideal_case)
        self.ideal_case['id'] = 0
        self.ideal_case = self.is_load_is_gen(self.ideal_case)

        if self.verbose:
            print('\nideal case before we do anything\n')
            print('Bus matrix: ')
            print(self.ideal_case['bus'][:, 0:5])

        # Evaluate ideal state
        self.ideal_state = self.evaluate_state(self.ideal_case)

        if self.verbose:
            print('\nideal case after evaluating state\n')
            print('Bus matrix: ')
            print(self.ideal_case['bus'][:, 0:5])

            print('\nideal state (should not have nans because system is complete)\n')
            print(self.ideal_state)

        # Deconstruct the ideal case
        self.broken_case = self.deactivate_branches()

        # # Detect and isolate islands, identify blackout zone
        self.islands = dict()
        self.get_islands(self.broken_case)

        # Islands evalutated
        self.islands_evaluated = list()
        self.evaluate_islands()

        # Get current state
        self.current_state = self.evaluate_state(self.islands_evaluated)

        # Identify the disconnected system elements - uses the current state variable and islands
        self.action_list = dict()
        self.generate_action_list()

        # Initialize blackout connection list (list within a list)
        self.blackout_connections = list([[]])

    def convert_to_mpc(self):
        # Converts the evaluated islands back to a matpower case so it can be ran again
        count = 0
        for island in make_iterable(self.islands_evaluated):
            obj = octave.opf_model(island)
            self.islands[count] = octave.get_mpc(obj)
            count += 1

    def generate_action_list(self):

        """
        The action list will contain all elements in blackout area plus disabled elements within energized islands

        """

        # Initialize disconnected elements dictionary
        self.action_list = {'lines': np.empty((0, 2)),
                            'fixed loads': np.empty((0, 1)),
                            'dispatch loads': np.empty((0, 1)),
                            'generators': np.empty((0, 1))}

        # Use current state to generate action list!
        # We have defined all disabled elements in the state as zeros, so we index

        line_ind = (self.current_state['real inj'][:, -1] == 0).reshape(-1)
        self.action_list['lines'] = self.current_state['real inj'][line_ind, 0:2]

        fixed_load_ind = (self.current_state['fixed load'][:, -1] == 0).reshape(-1)
        self.action_list['fixed loads'] = self.current_state['fixed load'][fixed_load_ind, 0]

        dispatch_load_ind = (self.current_state['dispatch load'][:, -1] == 0).reshape(-1)
        self.action_list['dispatch loads'] = self.current_state['dispatch load'][dispatch_load_ind, 0]

        gen_ind = (self.current_state['real gen'][:, -1] == 0).reshape(-1)
        self.action_list['generators'] = self.current_state['real gen'][gen_ind, 0]

    def initialize_state(self):

        if self.verbose:
            print('Initializing state \n')

        # The state arrays within the dictionary contain: id, values, island, status
        # Note that I am deepcopying the ideal caase

        gen_ind = (octave.isload(self.ideal_case['gen']) == 0).reshape((-1,))
        real_gen = deepcopy(self.ideal_case['gen'][gen_ind, :])
        real_gen = real_gen[:, 0:4]
        real_gen[:, 1:] = np.nan

        d_load_ind = (octave.isload(self.ideal_case['gen']) == 1).reshape((-1,))
        dispatch_load = deepcopy(self.ideal_case['gen'][d_load_ind, :])  # Bus, active power
        dispatch_load = dispatch_load[:, 0:4]
        dispatch_load[:, 1:] = np.nan

        f_load_ind = np.any(self.ideal_case['bus'][:, 2:4] > 0, axis=1)
        fixed_load = deepcopy(self.ideal_case['bus'][f_load_ind, :])
        fixed_load = fixed_load[:, 0:4]
        fixed_load[:, 1:] = np.nan

        real_inj = deepcopy(self.ideal_case['branch'][:, 0:5])
        real_inj[:, 2:] = np.nan
        reactive_inj = deepcopy(self.ideal_case['branch'][:, 0:5])
        reactive_inj[:, 2:] = np.nan

        bus_voltage_ang = deepcopy(self.ideal_case['bus'][:, 0:4])
        bus_voltage_ang[:, 1:] = np.nan

        state = {'real gen': real_gen,
                 'dispatch load': dispatch_load,
                 'fixed load': fixed_load,
                 'real inj': real_inj,
                 'reactive inj': reactive_inj,
                 'bus voltage angle': bus_voltage_ang,
                 'losses': 0}

        return state

    def evaluate_islands(self):

        if self.verbose:
            print('Evaluating islands \n')

        # Important note: When runopf is executed, the gencost matrix is destroyed. To remedy this, I save the matrix
        # and overwrite the result with this prior gencost matrix

        # Loop through the islands
        self.islands_evaluated = list()  # Re-initialize (we need to evaluate islands between actions)
        for island in list(self.islands.values()):

            # Only run for islands with both load and generation
            if island['is_gen'] and island['is_load']:
                # print('island id: %s' % island['id'])
                # print(island['bus'][:, 0:2])
                gencost = deepcopy(island['gencost'])
                result = octave.runopf(island, mp_opt)
                result = self.get_losses(result)
                result['gencost'] = gencost
                self.islands_evaluated.append(result)

            else:
                island['losses'] = 0
                self.islands_evaluated.append(island)

    def evaluate_state(self, island_list):

        if self.verbose:
            print('\nEvaluating state \n')

        # Initialize the current state dictionary (has same elements as the ideal)
        state = self.initialize_state()

        # Loop through islands and collect info
        for island in make_iterable(island_list):

            if self.verbose:
                print('\nExtracting info from island %s' % island['id'])

            # If there is both generation and load
            if island['is_gen'] and island['is_load']:

                # Fill in generator states for island i
                gen_ind = make_iterable(octave.isload(island['gen']) == 0).reshape((-1,))
                if self.verbose:
                    print('\nGenerator true:')
                    print(gen_ind)
                for bus_id in island['gen'][gen_ind, 0]:
                    ind1 = (state['real gen'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['gen'][gen_ind, 0] == bus_id).reshape((-1,))
                    state['real gen'][ind1, 1] = island['gen'][gen_ind, 1][ind2]
                    state['real gen'][ind1, 2] = island['id']
                    state['real gen'][ind1, 3] = island['gen'][gen_ind, 7][ind2]  # Gen status

                # Fill in dispatchable load states for island i
                d_load_ind = make_iterable(octave.isload(island['gen']) == 1).reshape((-1,))
                if self.verbose:
                    print('\nDispatchable load true:')
                    print(d_load_ind)
                for bus_id in island['gen'][d_load_ind, 0]:
                    ind1 = (state['dispatch load'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['gen'][d_load_ind, 0] == bus_id).reshape((-1,))
                    state['dispatch load'][ind1, 1] = island['gen'][d_load_ind, 1][ind2]
                    state['dispatch load'][ind1, 2] = island['id']
                    state['dispatch load'][ind1, 3] = island['gen'][d_load_ind, 7][ind2]  # gen/load status

                # Fill fixed load states for island i
                f_load_ind = make_iterable(np.any(island['bus'][:, 2:4] > 0, axis=1)).reshape((-1,))
                if self.verbose:
                    print('\nFixed load true:')
                    print(f_load_ind)
                    print('\nBus id, type and demand:')
                    print(island['bus'][:, 0:4])

                for bus_id in island['bus'][f_load_ind, 0]:
                    ind1 = (state['fixed load'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['bus'][f_load_ind, 0] == bus_id).reshape((-1,))
                    state['fixed load'][ind1, 1] = island['bus'][f_load_ind, 2][ind2]
                    state['fixed load'][ind1, 2] = island['id']
                    state['fixed load'][ind1, 3] = 1  # Fixed load is always on in energized island

                # Fill real injection to each line for island i
                for from_to in island['branch'][:, [0, 1, 13, 14]]:
                    ind1 = np.all(state['real inj'][:, 0:2] == from_to[0:2], axis=1)
                    ind2 = np.all(island['branch'][:, 0:2] == from_to[0:2], axis=1)
                    state['real inj'][ind1, 2] = from_to[2]
                    state['reactive inj'][ind1, 2] = from_to[3]
                    state['real inj'][ind1, 3] = island['id']
                    state['reactive inj'][ind1, 3] = island['id']
                    state['real inj'][ind1, 4] = island['branch'][ind2, 10]
                    state['reactive inj'][ind1, 4] = island['branch'][ind2, 10]  # Branch status

                # Fill bus voltage angle for island i
                for bus_id in island['bus'][:, 0]:
                    ind1 = (state['bus voltage angle'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['bus'][:, 0] == bus_id).reshape((-1,))
                    state['bus voltage angle'][ind1, 1] = island['bus'][ind2, 8]
                    state['bus voltage angle'][ind1, 2] = island['id']
                    state['bus voltage angle'][ind1, 3] = 1  # Status is always on in energized islands

            else:  # If either generation or load is missing

                # Fill in generator states for island i
                if len(island['gen']) > 0:
                    gen_ind = make_iterable(octave.isload(island['gen']) == 0).reshape((-1,))
                    for bus_id in island['gen'][gen_ind, 0]:
                        ind1 = (state['real gen'][:, 0] == bus_id).reshape((-1,))
                        state['real gen'][ind1, 1] = 0
                        state['real gen'][ind1, 2] = island['id']
                        state['real gen'][ind1, 3] = 0  # Gen status

                    # Fill in dispatchable load states for island i
                    d_load_ind = make_iterable(octave.isload(island['gen']) == 1).reshape((-1,))
                    for bus_id in island['gen'][d_load_ind, 0]:
                        ind1 = (state['dispatch load'][:, 0] == bus_id).reshape((-1,))
                        state['dispatch load'][ind1, 1] = 0
                        state['dispatch load'][ind1, 2] = island['id']
                        state['dispatch load'][ind1, 3] = 0  # gen/load status
                        # Set gen status in get_island

                # Fill fixed load states for island i
                if len(island['bus']) > 0:
                    f_load_ind = make_iterable(np.any(island['bus'][:, 2:4] > 0, axis=1)).reshape((-1,))
                    for bus_id in island['bus'][f_load_ind, 0]:
                        ind1 = (state['fixed load'][:, 0] == bus_id).reshape((-1,))
                        state['fixed load'][ind1, 1] = 0
                        state['fixed load'][ind1, 2] = island['id']
                        state['fixed load'][ind1, 3] = 0  # Fixed load in blackout is off

                    # Fill bus voltage angle for island i
                    for bus_id in island['bus'][:, 0]:
                        ind1 = (state['bus voltage angle'][:, 0] == bus_id).reshape((-1,))
                        state['bus voltage angle'][ind1, 1] = 0
                        state['bus voltage angle'][ind1, 2] = island['id']
                        state['bus voltage angle'][ind1, 3] = 0

                # Fill real injection to each line for island i
                if len(island['branch']) > 0:
                    for from_to in island['branch'][:, [0, 1, 13, 14]]:
                        ind1 = np.all(state['real inj'][:, 0:2] == from_to[0:2], axis=1)
                        state['real inj'][ind1, 2] = 0
                        state['reactive inj'][ind1, 2] = 0
                        state['real inj'][ind1, 3] = island['id']
                        state['reactive inj'][ind1, 3] = island['id']
                        state['real inj'][ind1, 4] = 0
                        state['reactive inj'][ind1, 4] = 0

            # Aggregate losses
            state['losses'] += island['losses']

        return state

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

        if self.verbose:
            print('\nExtracting islands \n')

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
                                    'losses': 0,
                                    'id': -1}
        count = 0
        for island in make_iterable(islands):
            if self.verbose:
                print('Extracting island %s' % island['id'])
                print('gen: %s \nload: %s' % (island['is_gen'], island['is_load']))

            # If there is both generation and loads
            if island['is_gen'] and island['is_load']:
                if self.verbose:
                    print('Island is energized')
                # Does island have a reference bus?  Set ref as bus with highest unused capacity
                if not np.any(island['bus'][:, 1] == 3):  # True if reference bus is missing
                    if self.verbose:
                        print('Adding reference bus')

                    # Find bus with largest unused capacity
                    largest = np.argmax(island['gen'][:, 8] - island['gen'][:, 1])
                    bus = island['gen'][largest, 0]
                    bus_index = island['bus'][:, 0] == bus

                    # Set bus as reference
                    island['bus'][bus_index, 1] = 3
                    island['slack_ind'] = np.where(island['bus'][:, 1] == 3)

                # Add energized island to the islands dictionary
                island['id'] = count
                self.islands['%s' % count] = island

                count += 1

            else:  # Gen or loads missing: blackout islands

                if self.verbose:
                    print('Island is in blackout')

                # Deconstruct island and place its elements in blackout zone
                self.islands['blackout']['bus'] = np.append(self.islands['blackout']['bus'],
                                                            island['bus'], axis=0)
                self.islands['blackout']['branch'] = np.append(self.islands['blackout']['branch'],
                                                               island['branch'], axis=0)
                self.islands['blackout']['gen'] = np.append(self.islands['blackout']['gen'],
                                                            island['gen'], axis=0)
                self.islands['blackout']['gencost'] = np.append(self.islands['blackout']['gencost'],
                                                                island['gencost'], axis=0)

        if self.verbose:
            print('\nExtracting blackout area')
            print('Using evaluate_state to uncover what is under blackout')

        # Add left over blackout elements! We need to evaluate the state and check for nans
        state = self.evaluate_state(list(self.islands.values()))

        # Populate blackout buses and set status
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
        gen_flag = np.concatenate((state['real gen'], state['dispatch load']), axis=0)
        gen_ind = np.isnan(gen_flag[:, 1]).reshape((-1,))
        gen_id = gen_flag[gen_ind, 0]
        for g_id in gen_id:
            ind1 = (self.ideal_case['gen'][:, 0] == g_id).reshape((-1,))
            self.islands['blackout']['gen'] = np.append(self.islands['blackout']['gen'],
                                                        self.ideal_case['gen'][ind1, :], axis=0)
            self.islands['blackout']['gencost'] = np.append(self.islands['blackout']['gencost'],
                                                            self.ideal_case['gencost'][ind1, :], axis=0)

        # Set statuses in blackout to zero
        self.islands['blackout']['branch'][:, 10] = 0
        self.islands['blackout']['gen'][:, 7] = 0

        if self.verbose:
            print('Island summary\n')
            for island in list(self.islands.values()):
                print('Island %s summary:' % island['id'])
                print('Bus matrix:')
                print(island['bus'][:, 0:4])
                print('Branch matrix:')
                print(island['branch'][:, [0, 1, 10]])
                print('\n')

    def visualize_state(self, state_list, fig_num=1):

        color_map = {0: 'black',
                     1: 'green'}

        # Initialize figure
        fig = plt.figure(fig_num, figsize=(12, 12))
        ax1 = plt.subplot2grid((2, 2), (0, 0))
        ax2 = plt.subplot2grid((2, 2), (0, 1))
        ax3 = plt.subplot2grid((2, 2), (1, 0), colspan=2)

        # Generator state plot
        gen_max = self.ideal_case['gen'][(octave.isload(self.ideal_case['gen']) == 0).reshape((-1)), 8].reshape((-1,))
        gen_ideal = self.ideal_state['real gen'][:, 1].reshape((-1,))
        gen_bus = self.ideal_state['real gen'][:, 0].reshape((-1,))
        cap_order = np.argsort(gen_max, axis=0, kind='quicksort')
        gen_width = 0.25
        gen_x = np.arange(len(gen_max))
        ax1.bar(gen_x - gen_width / 2, gen_ideal[cap_order], gen_width, align='center', alpha=0.9, color='blue')
        ax1.set_xticks(gen_x)
        ax1.set_xticklabels(['bus %d' % i for i in gen_bus[cap_order]])
        plt.title('Generator schedule')
        ax1.legend(['Generator limit', 'Ideal state', 'Current state'], loc='upper left')
        ax1.set_ylabel('Power (MW)')

        # Load state plot
        d_load_ideal = -self.ideal_state['dispatch load'][:, 1].reshape((-1,))
        d_load_bus = self.ideal_state['dispatch load'][:, 0].reshape((-1,))
        d_load_order = np.argsort(d_load_ideal, axis=0, kind='quicksort')

        f_load_ideal = self.ideal_state['fixed load'][:, 1].reshape((-1,))
        f_load_bus = self.ideal_state['fixed load'][:, 0].reshape((-1,))
        f_load_order = np.argsort(f_load_ideal, axis=0, kind='quicksort')

        load_width = 0.5
        load_x1 = np.arange(len(d_load_ideal))
        load_x2 = np.arange(len(load_x1) + 1, len(load_x1) + 1 + len(f_load_ideal))
        ticks = np.concatenate((['b %d' % i for i in d_load_bus[d_load_order]], ['b %d' % i for i in f_load_bus[f_load_order]]))
        ax2.set_xticklabels(ticks)
        ax2.set_xticks(np.concatenate((load_x1, load_x2)))
        plt.title('Load Profile')
        ax2.legend(['Ideal load', 'Current load'], loc='upper left')
        ax2.set_ylabel('Power (MW)')

        # Line state plot
        mva_rating = self.ideal_case['branch'][:, 5].reshape((-1,))
        real_inj_ideal = np.abs(self.ideal_state['real inj'][:, 2].reshape((-1,)))
        real_inj_buses = np.abs(self.ideal_state['real inj'][:, 0:2].reshape((-1, 2)))
        line_order = np.argsort(mva_rating, axis=0, kind='quicksort')
        line_width = 0.25
        line_x = np.arange(len(mva_rating))
        ax3.bar(line_x - line_width / 2, real_inj_ideal[line_order], line_width, align='center', alpha=0.9,color='blue')
        ax3.set_xticks(line_x)
        ticks = ['%d - %d' % (i[0], i[1]) for i in real_inj_buses[line_order]]
        ax3.set_xticklabels(ticks)
        plt.title('Line loadings')
        ax3.legend(['Line limit', 'Ideal load', 'Current load'], loc='upper left')
        ax3.set_ylabel('Power (MW)')
        plt.xlim([-1, len(line_order)])

        plt.tight_layout()

        # Init dynamic plot objects
        gen_cap, = ax1.bar([], [])
        gen_curr, = ax1.bar([], [])
        d_ideal, = ax2.bar([], [])
        d_curr, = ax2.bar([], [])
        f_ideal, = ax2.bar([], [])
        f_curr, = ax2.bar([], [])
        line_rating, = ax3.bar([], [])
        line_curr, = ax3.bar([], [])

        dyn_objects = [gen_cap, gen_curr, d_ideal, d_curr, f_ideal, f_curr, line_rating, line_curr]

        def update(frame):

            # Clear the last set of data
            for obj in dyn_objects:
                obj.clear()

            # Generator state plot dynamic data
            gen_current = state_list[frame]['real gen'][:, 1].reshape((-1,))
            gen_island = state_list[frame]['real gen'][cap_order, -1]
            dyn_objects[0], = ax1.bar(gen_x, gen_max[cap_order], gen_width*2, align='center', alpha=0.3, color=[color_map[ind] for ind in gen_island])
            dyn_objects[1], = ax1.bar(gen_x+gen_width/2, gen_current[cap_order], gen_width, align='center', alpha=0.9, color='red')

            # Load state plot dynamic data
            d_load_current = -state_list[frame]['dispatch load'][:, 1].reshape((-1,))
            d_load_island = state_list[frame]['dispatch load'][d_load_order, -1]
            f_load_current = state_list[frame]['fixed load'][:, 1].reshape((-1,))
            f_load_island = state_list[frame]['fixed load'][f_load_order, -1]
            dyn_objects[2], = ax2.bar(load_x1, d_load_ideal[d_load_order], load_width, align='center', alpha=0.2, color=[color_map[ind] for ind in d_load_island])
            dyn_objects[3], = ax2.bar(load_x1, d_load_current[d_load_order], load_width, align='center', alpha=0.9, color=[color_map[ind] for ind in d_load_island])
            dyn_objects[4], = ax2.bar(load_x2, f_load_ideal[f_load_order], load_width, align='center', alpha=0.2, color=[color_map[ind] for ind in f_load_island])
            dyn_objects[5], = ax2.bar(load_x2, f_load_current[f_load_order], load_width, align='center', alpha=0.9, color=[color_map[ind] for ind in f_load_island])

            # Line state plot dynamic data
            real_inj_current = np.abs(state_list[frame]['real inj'][:, 2].reshape((-1,)))
            line_island = state_list[frame]['real inj'][line_order, -1]
            dyn_objects[6], = ax3.bar(line_x, mva_rating[line_order], line_width*2, align='center', alpha=0.3, color=[color_map[ind] for ind in line_island])
            dyn_objects[7], = ax3.bar(line_x+line_width/2, real_inj_current[line_order], line_width, align='center', alpha=0.9, color='red')

            if state_list[frame]['Title']:
                plt.suptitle(state_list[frame]['Title'], labelsize=18)
            else:
                plt.suptitle('')

            time.sleep(0.5)

            return dyn_objects

        ani = animation.FuncAnimation(fig, update, frames=len(state_list))

        plt.show()

        # for state in state_list:
        #
        #     # Generator state plot dynamic data
        #     gen_current = state['real gen'][:, 1].reshape((-1,))
        #     gen_island = state['real gen'][cap_order, -1]
        #     gen_cap, = ax1.bar(gen_x, gen_max[cap_order], gen_width*2, align='center', alpha=0.3, color=[color_map[ind] for ind in gen_island])
        #     gen_curr, = ax1.bar(gen_x+gen_width/2, gen_current[cap_order], gen_width, align='center', alpha=0.9, color='red')
        #
        #     # Load state plot dynamic data
        #     d_load_current = -state['dispatch load'][:, 1].reshape((-1,))
        #     d_load_island = state['dispatch load'][d_load_order, -1]
        #     f_load_current = state['fixed load'][:, 1].reshape((-1,))
        #     f_load_island = state['fixed load'][f_load_order, -1]
        #     d_ideal, = ax2.bar(load_x1, d_load_ideal[d_load_order], load_width, align='center', alpha=0.2, color=[color_map[ind] for ind in d_load_island])
        #     d_curr, = ax2.bar(load_x1, d_load_current[d_load_order], load_width, align='center', alpha=0.9, color=[color_map[ind] for ind in d_load_island])
        #     f_ideal, = ax2.bar(load_x2, f_load_ideal[f_load_order], load_width, align='center', alpha=0.2, color=[color_map[ind] for ind in f_load_island])
        #     f_curr, = ax2.bar(load_x2, f_load_current[f_load_order], load_width, align='center', alpha=0.9, color=[color_map[ind] for ind in f_load_island])
        #
        #
        #     # Line state plot dynamic data
        #     real_inj_current = np.abs(state['real inj'][:, 2].reshape((-1,)))
        #     line_island = state['real inj'][line_order, -1]
        #     line_rating, = ax3.bar(line_x, mva_rating[line_order], line_width*2, align='center', alpha=0.3, color=[color_map[ind] for ind in line_island])
        #     line_curr, = ax3.bar(line_x+line_width/2, real_inj_current[line_order], line_width, align='center', alpha=0.9, color='red')
        #
        #
        #     if state['Title']:
        #         plt.suptitle(state['Title'])
        #     else:
        #         plt.suptitle('')
        #
        #     time.sleep(1.5)

    def action_line(self, bus_ids):
        """Line connection case list:

        1. Line within an energized island is enabled
            * Very common, simplest
            * Easy to implement, just switch on
            * SPA constrains need to be set
        2. Line between 2 energized islands is enabled
            * Bit more complex than within island case
            * Need to consolidate the islands into one
            * Need to remove one of the slack buses
            * Assume the SPAs are synchronized
        3. Line between an energized island and blackout area is enabled
            * Consult the connection list to see if there are further connections there
            * Add the "left over" bus(s) to the island
            * Add the "left over" branch(s) to the island and enable
            * Add any generation or dispatchable load to the island, but don't enable, this occurs as separate action
            * If there is new fixed load, disable it, enabling it is a separate action
            * Don't need to set SPA constraint, we are energizing a bus
        4. Line within blackout area is enabled
            * I need to implement a connection list to monitor what has been connected
            * These buses will be connected and added to the connection list
        """

        island_map = {-1: 'blackout',
                      0: '0',
                      1: '1',
                      2: '2',
                      3: '3'}

        # Verify action is available!
        ind = np.all(self.action_list['lines'] == bus_ids, axis=1)
        if np.sum(ind) != 1:
            print('Buses not on action list!')
            return

        # Remove line from the action list
        self.action_list['lines'] = np.delete(self.action_list['lines'], np.where(ind), axis=0)

        # Initialize list of states
        state_list = list()

        # What islands do the buses reside on?
        bus_ind_1 = (self.current_state['bus voltage angle'][:, 0] == bus_ids[0]).reshape(-1)
        bus_ind_2 = (self.current_state['bus voltage angle'][:, 0] == bus_ids[1]).reshape(-1)
        island_1 = int(self.current_state['bus voltage angle'][bus_ind_1, 2])
        island_2 = int(self.current_state['bus voltage angle'][bus_ind_2, 2])

        if self.verbose:
            print('\nEnabling branch between buses %s and %s' % (bus_ids[0], bus_ids[1]))
            print('Connection between island(s) %s and %s' % (island_1, island_2))

        if island_1 == island_2 and island_1 != -1:
            # Need to generate a list of states here, there are several steps performed

            if self.verbose:
                print('Case: within energized island')

            # Take preliminary snapshot of the system
            prelim_state = self.evaluate_state(self.islands_evaluated)
            prelim_state['Title'] = 'Preliminary state'  # Shows up on plot
            state_list.append(prelim_state)

            # Set opf constraint to SPA diff
            branch_ind = np.all(self.islands[island_map[island_1]]['branch'][:, 0:2] == bus_ids, axis=1)
            print(branch_ind)
            self.islands[island_map[island_1]] = set_opf_constraints(test_case=self.islands[island_map[island_1]],
                                                                     set_branch=branch_ind,
                                                                     max_SPA=20,
                                                                     set_gen=False,
                                                                     set_loads=False)
            # Run opf on the islands
            self.evaluate_islands()
            print(island_1)
            print(branch_ind)
            self.islands_evaluated[island_1]['branch'][branch_ind, 10] = 1  # For animation
            reschedule_state = self.evaluate_state(self.islands_evaluated)
            reschedule_state['Title'] = 'Rescheduling for connection of branch %s - %s' % (bus_ids[0], bus_ids[1])
            state_list.append(reschedule_state)

            # Close the line and restore the SPA diff constraint
            self.islands[island_map[island_1]]['branch'][branch_ind, 10] = 1
            self.islands[island_map[island_1]] = set_opf_constraints(test_case=self.islands[island_map[island_1]],
                                                                     set_branch=branch_ind,
                                                                     max_SPA=360,
                                                                     set_gen=False,
                                                                     set_loads=False)
            # Run opf for final steady state
            self.evaluate_islands()
            after_connection_state = self.evaluate_state(self.islands_evaluated)
            after_connection_state['Title'] = 'State after line connection'
            state_list.append(after_connection_state)

        elif island_1 == island_2 and island_1 == -1:
            # Don't need to create a state list in this case, just record whats connected!

            if self.verbose:
                print('Case: within blackout area')

            # Check connections list for the buses in question
            for connections in make_iterable(self.blackout_connections):
                ind = np.array([i in connections for i in bus_ids])
                if any(ind):  # Are any buses in question in connections?
                    unique_bus = bus_ids[~ind]  # Detects which bus is unique to connections
                    connections.append(unique_bus)
                    break

            # If no connections found, start a new connection list:
            self.blackout_connections.append(bus_ids[0])
            self.blackout_connections.append(bus_ids[1])

        elif island_1 != island_2 and (island_1 != -1 and island_2 != -1):
            if self.verbose:
                print('Case: connecting two energized islands')

        #     print('Connecting islands %s and %s \n' % (island_1, island_2))
        #
        #     # Append all of island 2 to island 1
        #     # self.islands[island_1] = deepcopy(self.islands[island_1])
        #     self.islands[island_1]['bus'] = np.append(self.islands[island_1]['bus'], self.islands[island_2]['bus'], axis=0)
        #     self.islands[island_1]['branch'] = np.append(self.islands[island_1]['branch'], self.islands[island_2]['branch'], axis=0)
        #     self.islands[island_1]['gen'] = np.append(self.islands[island_1]['gen'], self.islands[island_2]['gen'], axis=0)
        #     self.islands[island_1]['gencost'] = np.append(self.islands[island_1]['gencost'], self.islands[island_2]['gencost'], axis=0)
        #
        #     # Delete island 2
        #     self.islands = np.delete(self.islands, island_2)
        #
        #     # Remember: to remove the weaker of the swing buses!
        #     # ind = self.islands[island_1]['bus'][:, 1] == 3
        #     # print(ind)
        #     # bus_id = self.islands[island_1]['bus'][ind, 0]
        #     # print(bus_id)
        #     # gen_ind = self.islands[island_1]['gen'][:, 0] == bus_id
        #     # print(gen_ind)
        #     # gen_cap = self.islands[island_1]['gen'][gen_ind, 8]
        #     # print(gen_cap)
        #     # gen_weak_ind = self.islands[island_1]['gen'][:, 8] == np.min(gen_cap)
        #     # print(gen_weak_ind)
        #     # gen_weak_bus_id = self.islands[island_1]['gen'][gen_weak_ind, 0]
        #     # print(gen_weak_bus_id)
        #     # weak_bus_ind = self.islands[island_1]['bus'][:, 0] == gen_weak_bus_id
        #     # print(weak_bus_ind)
        #     #
        #     # # Set weak bus type to 1 (PQ bus)
        #     # self.islands[island_1]['bus'][weak_bus_ind, 1] = 1

        elif island_1 != island_2 and (island_1 == -1 or island_2 == -1):
            if self.verbose:
                print('Case: connecting non-energized bus to energized island')
        else:
            if self.verbose:
                print('SOMEHTHING IS NOT RIGHT')


        # Feed the objective function state list.

        return state_list

        # for i, island in enumerate(make_iterable(self.islands)):
        #     if np.any(island['bus'][:, 0] == bus_ids[0]):
        #         island_1 = i
        # print('island 1: %s\n' % island_1)

        # # Check islands to find bus 2
        # island_2 = None
        # for i, island in enumerate(make_iterable(self.islands)):
        #     if np.any(island['bus'][:, 0] == bus_ids[1]):
        #         island_2 = i
        # print('island 2: %s\n' % island_2)

        # If islands are same, its simple
        # if island_1 == island_2 and island_1 is not None:
        #     print('Line does not connect islands\n')
        #     ind = np.all(self.islands[island_1]['branch'][:, 0:2] == bus_ids, axis=1)
        #     # print(self.islands[island_1]['branch'][:, 0:2])
        #     # print(self.islands[island_1]['branch'][:, 0:2] == bus_ids)
        #     # print(ind)
        #     # print('\n')
        #
        #     # Need to set opf contraints and run opf
        #     self.islands[island_1]['branch'][ind, 10] = 1  # Change branch status to 1 (in-service)
        #
        #     # Show reconection of line
        #     print('Connected lines')
        #     for island in make_iterable(self.islands):
        #         print(island['branch'][:, 10])
        #
        # # In these cases, add the line and energize/enable the line to the island
        # # Turns out that in these cases, energizing a line with nothing on the None end, convergence failure occurs!!
        # # Convergence failure occured when connecting line 1-2, which is typically a very high load line...
        # # Current method worked fine on smaller lines.
        # # How do I fix this? Add a load or gen at the new bus?
        # elif island_1 is None and island_2 is not None:
        #     print('Line connects to None\n')
        #     # Add the missing bus (bus 1) from ideal case
        #     ind = self.ideal_case['bus'][:, 0] == bus_ids[0]
        #     print(ind)
        #     self.islands[island_2]['bus'] = np.append(self.islands[island_2]['bus'],
        #                                               self.ideal_case['bus'][ind, :], axis=0)
        #
        #     # Add the missing branch from ideal case
        #     ind = np.all(self.ideal_case['branch'][:, 0:2] == bus_ids, axis=1)
        #     print(ind)
        #     self.islands[island_2]['branch'] = np.append(self.islands[island_2]['branch'],
        #                                                  self.ideal_case['branch'][ind, :], axis=0)
        #
        # elif island_2 is None and island_1 is not None:
        #     print('Line connects to None\n')
        #     # Add the missing bus (bus 2) from ideal case
        #     ind = self.ideal_case['bus'][:, 0] == bus_ids[1]
        #     print(ind)
        #     self.islands[island_1]['bus'] = np.append(self.islands[island_1]['bus'],
        #                                               self.ideal_case['bus'][ind, :], axis=0)
        #
        #     # Add the missing branch from ideal case
        #     ind = np.all(self.ideal_case['branch'][:, 0:2] == bus_ids, axis=1)
        #     print(ind)
        #     self.islands[island_1]['branch'] = np.append(self.islands[island_1]['branch'],
        #                                                  self.ideal_case['branch'][ind, :], axis=0)
        #
        # # If islands differ, we have to combine their case structures!
        # # TODO: this needs debugging
        # else:
        #     print('Connecting islands %s and %s \n' % (island_1, island_2))
        #
        #     # Append all of island 2 to island 1
        #     # self.islands[island_1] = deepcopy(self.islands[island_1])
        #     self.islands[island_1]['bus'] = np.append(self.islands[island_1]['bus'], self.islands[island_2]['bus'], axis=0)
        #     self.islands[island_1]['branch'] = np.append(self.islands[island_1]['branch'], self.islands[island_2]['branch'], axis=0)
        #     self.islands[island_1]['gen'] = np.append(self.islands[island_1]['gen'], self.islands[island_2]['gen'], axis=0)
        #     self.islands[island_1]['gencost'] = np.append(self.islands[island_1]['gencost'], self.islands[island_2]['gencost'], axis=0)
        #
        #     # Delete island 2
        #     self.islands = np.delete(self.islands, island_2)
        #
        #     # Remember: to remove the weaker of the swing buses!
        #     # ind = self.islands[island_1]['bus'][:, 1] == 3
        #     # print(ind)
        #     # bus_id = self.islands[island_1]['bus'][ind, 0]
        #     # print(bus_id)
        #     # gen_ind = self.islands[island_1]['gen'][:, 0] == bus_id
        #     # print(gen_ind)
        #     # gen_cap = self.islands[island_1]['gen'][gen_ind, 8]
        #     # print(gen_cap)
        #     # gen_weak_ind = self.islands[island_1]['gen'][:, 8] == np.min(gen_cap)
        #     # print(gen_weak_ind)
        #     # gen_weak_bus_id = self.islands[island_1]['gen'][gen_weak_ind, 0]
        #     # print(gen_weak_bus_id)
        #     # weak_bus_ind = self.islands[island_1]['bus'][:, 0] == gen_weak_bus_id
        #     # print(weak_bus_ind)
        #     #
        #     # # Set weak bus type to 1 (PQ bus)
        #     # self.islands[island_1]['bus'][weak_bus_ind, 1] = 1
        #
        # # Update disconnected element dictionary
        # ind = np.all(self.disconnected_elements['lines'][:, 0:2] == bus_ids, axis=1)
        # self.disconnected_elements['lines'] = np.delete(self.disconnected_elements['lines'], np.where(ind), 0)

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
