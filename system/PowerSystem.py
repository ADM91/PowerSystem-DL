from copy import deepcopy
from pprint import PrettyPrinter
import numpy as np
from copy import copy, deepcopy
import oct2py
from oct2py import Oct2Py
from system.line_connection_cases.between_blackout_energized import between_blackout_energized
from system.line_connection_cases.between_islands import between_islands
from system.line_connection_cases.within_energized import within_energized
from system.take_snapshot import take_snapshot
from auxiliary.reshape_gencost import reshape_gencost
from system.verify_state_feasibility import verify_state_feasibility
from system.adjust_power_factor import adjust_power_factor


def make_iterable(obj):
    if type(obj) == list:
        return obj
    elif type(obj) == oct2py.io.Cell:
        return obj.reshape((-1,))
    else:
        return np.array([obj])


class PowerSystem(object):

    def __init__(self, metadata, spad_lim=10, deactivated=1, verbose=1, verbose_state=0):

        # Instantiate octave instance
        self.octave = Oct2Py()
        self.octave.addpath('/home/alexander/Documents/MATLAB/matpower6.0')
        self.pp = PrettyPrinter(indent=4)
        self.deactivated = deactivated
        self.verbose = verbose
        self.verbose_state = verbose_state
        self.spad_lim = spad_lim
        self.current_state = None
        self.metadata = metadata
        self.dispatchable_loads = metadata['dispatchable_loads']
        self.mp_opt = metadata['mp_opt']
        self.island_map = {-1: 'blackout',
                           0: '0',
                           1: '1',
                           2: '2',
                           3: '3'}
        self.ideal_case = None
        self.ideal_state = None
        self.broken_case = None
        self.islands = dict()
        self.action_list = dict()

    def set_ideal_case(self, ideal_case):

        # Set the opf constraints on the ideal case, before deconstruction
        self.ideal_case = self.set_opf_constraints(ideal_case)
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
        if type(self.deactivated) == int:
            self.broken_case = self.random_deactivate()
        else:
            self.broken_case = self.indexed_deactivate()

        # Detect and isolate islands, identify blackout zone
        self.get_islands(self.broken_case)
        success = self.evaluate_islands()

        # Get current state
        self.current_state = self.evaluate_state(list(self.islands.values()))

        # Identify the disconnected system elements - uses the current state variable and islands
        self.generate_action_list()

        return success

    def reset(self):
        """Resets the class to its original degraded state"""

        # Deconstruct the ideal case
        if type(self.deactivated) == int:
            self.broken_case = self.random_deactivate()
        else:
            self.broken_case = self.indexed_deactivate()

        # Detect and isolate islands, identify blackout zone
        self.islands = dict()
        self.get_islands(self.broken_case)
        self.evaluate_islands()

        # Get current state
        self.current_state = self.evaluate_state(list(self.islands.values()))

        # Identify the disconnected system elements - uses the current state variable and islands
        self.action_list = dict()
        self.generate_action_list()

        # Initialize blackout connection list (list within a list)
        self.blackout_connections = {'buses': [],
                                     'lines': []}

    def revert(self, state, islands):
        """ Restores the system using previous islands and state data"""

        # Restore islands
        self.islands = copy(islands)

        # Get current state
        self.current_state = copy(state)

        # print('After revert (within the class)')
        # print(self.current_state['real inj'][17, [2, 4]])
        # print(self.islands['0']['branch'][17, 10:13])

    def generate_action_list(self):

        """
        The action list will contain all elements in blackout area plus disabled elements within energized islands

        """

        # Initialize disconnected elements dictionary
        self.action_list = {'line': np.empty((0, 2)),
                            'fixed load': np.empty((0, 1)),
                            'dispatch load': np.empty((0, 1)),
                            'gen': np.empty((0, 1))}

        # Use current state to generate action list!
        # We have defined all disabled elements in the state as zeros, so we index

        line_ind = (self.current_state['real inj'][:, -1] == 0).reshape(-1)
        self.action_list['line'] = deepcopy(self.current_state['real inj'][line_ind, 0:2])

        fixed_load_ind = (self.current_state['fixed load'][:, -1] == 0).reshape(-1)
        self.action_list['fixed load'] = deepcopy(self.current_state['fixed load'][fixed_load_ind, 0])

        dispatch_load_ind = (self.current_state['dispatch load'][:, -1] == 0).reshape(-1)
        self.action_list['dispatch load'] = deepcopy(self.current_state['dispatch load'][dispatch_load_ind, 0])

        gen_ind = (self.current_state['real gen'][:, -1] == 0).reshape(-1)
        self.action_list['gen'] = deepcopy(self.current_state['real gen'][gen_ind, 0])

    def initialize_state(self):

        if self.verbose:
            print('Initializing state \n')

        # The state arrays within the dictionary contain: id, values, island, status
        # Note that I am deepcopying the ideal caase

        gen_ind = (self.octave.isload(self.ideal_case['gen']) == 0).reshape((-1,))
        real_gen = deepcopy(self.ideal_case['gen'][gen_ind, :])
        real_gen = real_gen[:, 0:4]
        real_gen[:, 1:] = np.nan

        d_load_ind = (self.octave.isload(self.ideal_case['gen']) == 1).reshape((-1,))
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
        opf_success = 1
        pf_success = 1
        for key, island in list(self.islands.items()):

            # Only run for islands with both load and generation
            if island['is_gen'] and island['is_load']:
                # Evaluate the energized island with opf constraints
                gencost = deepcopy(island['gencost'])

                # Is there power factor discrepancy?
                success = verify_state_feasibility(self)
                if success == 0:
                    print('\npower factor failure prior to runopf!\nAdjusting power factor...\n')

                    # Adjust generator values if discrepancy
                    island['gen'] = adjust_power_factor(self.octave, island['gen'])

                try:

                    result = self.octave.runopf(island, self.mp_opt)
                    result = self.get_losses(result)
                except Exception as e:
                    print('\nError: %s' % e)
                    print('Could not prevent the power factor error, trying again:\n ')
                    # Adjust generator values if discrepancy
                    island['gen'] = adjust_power_factor(self.octave, island['gen'])
                    result = self.octave.runopf(island, self.mp_opt)
                    result = self.get_losses(result)
                    # print('\nbus matrix')
                    # print(island['bus'][:, [0,1,3,4]])
                    # print('\nbranch matrix')
                    # print(island['branch'][:, [0,1,10]])
                    # print('\ngen matrix')
                    # print(island['gen'][:, [0,1,2,3,4,8,9]])
                    # print('\ngencost matrix')
                    # print(island['gencost'])

                if result['success'] == 0:
                    opf_success = 0

                # Reset island data to the evaluated result
                # self.octave object/dynamic does not work, so we have to reconstruct the mpc from scratch (not that hard)
                island['bus'] = result['bus']
                island['branch'] = result['branch']
                island['gen'] = result['gen']
                island['gencost'] = gencost
                island['losses'] = result['losses']
                self.islands[key] = island

                # Is there power factor discrepancy?
                success = verify_state_feasibility(self)
                if success == 0:
                    pf_success = 0

            else:  # Blackout area gets returned as is
                island['losses'] = 0
                self.islands[key] = island

        print('opf success: %s, power factor success: %s' % (opf_success, pf_success))
        if opf_success and pf_success:
            return 1
        else:
            return 0

    def evaluate_state(self, island_list):

        if self.verbose_state:
            print('\nEvaluating state \n')

        # Initialize the current state dictionary (has same elements as the ideal)
        state = self.initialize_state()

        # Loop through islands and collect info
        for island in make_iterable(island_list):

            if self.verbose_state:
                print('\nExtracting info from island %s' % island['id'])

            # If there is both generation and load
            if island['is_gen'] and island['is_load']:

                # Fill in generator states for island i
                gen_ind = make_iterable(self.octave.isload(island['gen']) == 0).reshape((-1,))
                if self.verbose_state:
                    print('\nGenerator true:')
                    print(gen_ind)
                for bus_id in island['gen'][gen_ind, 0]:
                    ind1 = (state['real gen'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['gen'][gen_ind, 0] == bus_id).reshape((-1,))
                    state['real gen'][ind1, 1] = island['gen'][gen_ind, 1][ind2]
                    state['real gen'][ind1, 2] = island['id']
                    state['real gen'][ind1, 3] = island['gen'][gen_ind, 7][ind2]  # Gen status

                # Fill in the dispatchable load states for island i
                d_load_ind = make_iterable(self.octave.isload(island['gen']) == 1).reshape((-1,))
                if self.verbose_state:
                    print('\nDispatchable load true:')
                    print(d_load_ind)
                for bus_id in island['gen'][d_load_ind, 0]:
                    ind1 = (state['dispatch load'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['gen'][d_load_ind, 0] == bus_id).reshape((-1,))
                    state['dispatch load'][ind1, 1] = island['gen'][d_load_ind, 1][ind2]
                    state['dispatch load'][ind1, 2] = island['id']
                    state['dispatch load'][ind1, 3] = island['gen'][d_load_ind, 7][ind2]  # gen/load status

                # Fill fixed load states for island i (loads identified based on ideal case, island might have unserved load)
                f_load_ind = [np.any(self.ideal_case['bus'][ind[0], 2:4] > 0, axis=1) for ind in [np.where(island_bus == self.ideal_case['bus'][:, 0]) for island_bus in island['bus'][:, 0]]]
                f_load_ind = np.where(f_load_ind)[0]

                if self.verbose_state:
                    print('\nFixed load true:')
                    print(f_load_ind)
                    print('\nBus id, type and demand:')
                    print(island['bus'][:, 0:4])

                for bus_id in island['bus'][f_load_ind, 0]:
                    ind1 = (state['fixed load'][:, 0] == bus_id).reshape((-1,))
                    ind2 = (island['bus'][f_load_ind, 0] == bus_id).reshape((-1,))
                    state['fixed load'][ind1, 1] = island['bus'][f_load_ind, 2][ind2]  # Real power
                    state['fixed load'][ind1, 2] = island['id']                        # Island id
                    if np.any(island['bus'][f_load_ind, 2:4][ind2] > 0):
                        state['fixed load'][ind1, 3] = 1                               # On/off state
                    else:
                        state['fixed load'][ind1, 3] = 0

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
                    gen_ind = make_iterable(self.octave.isload(island['gen']) == 0).reshape((-1,))
                    for bus_id in island['gen'][gen_ind, 0]:
                        ind1 = (state['real gen'][:, 0] == bus_id).reshape((-1,))
                        state['real gen'][ind1, 1] = 0
                        state['real gen'][ind1, 2] = island['id']
                        state['real gen'][ind1, 3] = 0  # Gen status

                    # Fill in dispatchable load states for island i
                    d_load_ind = make_iterable(self.octave.isload(island['gen']) == 1).reshape((-1,))
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

    def random_deactivate(self):
        """
        Removes random lines from the system.
        """

        # Number of branches
        n = self.ideal_case['branch'].shape[0]

        # select random integers in range 0 : n-1
        remove = np.random.choice(n, size=self.deactivated, replace=False)

        # Create copy of case
        new_case = deepcopy(self.ideal_case)

        # Remove the line(s) from copy
        new_case['branch'][remove, 10] = 0

        new_case['disconnected'] = remove

        return new_case

    def indexed_deactivate(self):

        # Create copy of case
        new_case = deepcopy(self.ideal_case)

        remove = self.deactivated  # Must be true false array

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
        islands = self.octave.extract_islands(case)

        if self.verbose:
            for i in islands:
                print(i)
                # if len(i['gen']) > 0:
                #     print(i['gen'][:, [0,1,2,7]])

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

            # If there is both generation and load
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
                if len(island['bus']) < 0:
                    self.islands['blackout']['bus'] = np.append(self.islands['blackout']['bus'],
                                                                island['bus'], axis=0)
                if len(island['branch']) < 0:
                    self.islands['blackout']['branch'] = np.append(self.islands['blackout']['branch'],
                                                                   island['branch'], axis=0)
                # print(self.islands['blackout']['gen'])
                # print(island['gen'])
                if len(island['gen']) < 0:
                    self.islands['blackout']['gen'] = np.append(self.islands['blackout']['gen'],
                                                                island['gen'], axis=0)
                if len(island['gencost']) < 0:
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
        gen_ind = np.isnan(state['real gen'][:, 1]).reshape((-1,))
        gen_id = state['real gen'][gen_ind, 0]
        for g_id in gen_id:
            gen_ind = (self.octave.isload(self.ideal_case['gen']) == 0).reshape(-1)
            gen = self.ideal_case['gen'][gen_ind, :]
            gencost = self.ideal_case['gencost'][gen_ind, :]
            ind1 = (gen[:, 0] == g_id).reshape(-1,)
            self.islands['blackout']['gen'] = np.append(self.islands['blackout']['gen'],
                                                        gen[ind1, :], axis=0)
            self.islands['blackout']['gencost'] = np.append(self.islands['blackout']['gencost'],
                                                            gencost[ind1, :], axis=0)

        # Populate blackout dispatchable loads
        load_ind = np.isnan(state['dispatch load'][:, 1]).reshape((-1,))
        load_id = state['dispatch load'][load_ind, 0]
        for g_id in gen_id:
            gen_ind = (self.octave.isload(self.ideal_case['gen']) == 1).reshape(-1)  # index of dispatchable loads
            gen = self.ideal_case['gen'][gen_ind, :]
            gencost = self.ideal_case['gencost'][gen_ind, :]
            ind1 = (gen[:, 0] == g_id).reshape(-1,)
            self.islands['blackout']['gen'] = np.append(self.islands['blackout']['gen'],
                                                        gen[ind1, :], axis=0)
            self.islands['blackout']['gencost'] = np.append(self.islands['blackout']['gencost'],
                                                            gencost[ind1, :], axis=0)

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

        # Verify that action is available!
        ind = np.all(self.action_list['line'] == bus_ids, axis=1)
        if np.sum(ind) != 1:
            # print(self.action_list['line'])
            print('Buses not on action list!: %s' % bus_ids)
            return [], []

        # What islands do the buses reside on? First evaluate current state
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

            state_list, island_list = within_energized(self, island_1, bus_ids, self.spad_lim)

        # Deprecating the within_blackout function, its not practical to connect lines within blackout
        elif island_1 == island_2 and island_1 == -1:
            # Don't need to create a state list in this case, just record whats connected!
            if self.verbose:
                print('Case: within blackout area')
            return [], []

        elif island_1 != island_2 and (island_1 != -1 and island_2 != -1):
            if self.verbose:
                print('Case: Connecting energized islands %s and %s \n' % (island_1, island_2))

            # TODO: don't i have to supply the line linking the islands??
            state_list, island_list = between_islands(self, island_1, island_2)

        elif island_1 != island_2 and (island_1 == -1 or island_2 == -1):
            # There should be state collection here
            if self.verbose:
                print('Case: connecting non-energized bus to energized island')

            state_list, island_list = between_blackout_energized(self, island_1, island_2, bus_ids)

        else:
            if self.verbose:
                print('SOMETHING IS NOT RIGHT')
            return [], []

        # Ensure that current state variables has the most recent information
        if len(state_list) > 0:
            self.current_state = state_list[-1]

        # Feed the objective function state list.
        return state_list, island_list

    def action_fixed_load(self, bus_id):

        # Verify that action is available!
        ind = self.action_list['fixed load'] == bus_id
        if np.sum(ind) != 1:
            print('Load not on action list!')
            return [], []

        # Take preliminary snapshot of the system
        state_list, island_list = take_snapshot(self, 'Preliminary state', [], [])

        # What island does bus reside on?
        bus_ind = self.current_state['bus voltage angle'][:, 0] == bus_id
        island = int(self.current_state['bus voltage angle'][bus_ind, 2])

        if island == -1:
            # print('Can not activate fixed load within blackout area!')
            return [], []

        # Set the load on the island bus matrix
        island_bus_ind = (self.islands[self.island_map[island]]['bus'][:, 0] == bus_id).reshape(-1)
        ideal_bus_ind = (self.ideal_case['bus'][:, 0] == bus_id).reshape(-1)
        self.islands[self.island_map[island]]['bus'][island_bus_ind, 2:4] = self.ideal_case['bus'][ideal_bus_ind, 2:4]

        # Evaluate islands with new load
        success = self.evaluate_islands()
        if success == 0:
            return [], []

        # Take snapshot
        title = 'Connecting fixed load on bus %s' % int(bus_id)
        state_list, island_list = take_snapshot(self, title, state_list, island_list)

        # Ensure that current state variable has the most recent information
        self.current_state = state_list[-1]

        # Feed the objective function state list.
        return state_list, island_list

    def action_dispatch_load(self, bus_id):

        # Verify that action is available!
        ind = self.action_list['dispatch load'] == bus_id
        if np.sum(ind) != 1:
            print('Dispatchable load not on action list!')
            return [], []

        # Take preliminary snapshot of the system
        state_list, island_list = take_snapshot(self, 'Preliminary state', [], [])

        # What islands does the bus reside on?
        bus_ind = self.current_state['bus voltage angle'][:, 0] == bus_id
        island = int(self.current_state['bus voltage angle'][bus_ind, 2])

        if island == -1:
            print('Can not activate dispatchable load within blackout area!')
            return [], []

        # Activate the dispatchable load
        # I have to be careful to select the load not generator (a generator may reside on the same bus)
        load_ind = np.where(self.octave.isload(self.islands[self.island_map[island]]['gen']) == 1)[0]  # indicies of loads
        bus_ind = np.where(self.islands[self.island_map[island]]['gen'][load_ind, 0] == bus_id)  # index to load_ind
        self.islands[self.island_map[island]]['gen'][load_ind[bus_ind], 7] = 1

        # Evaluate islands with new load
        success = self.evaluate_islands()
        if success == 0:
            return [], []

        # Take snapshot
        title = 'Connecting dispatchable load on bus %s' % int(bus_id)
        state_list, island_list = take_snapshot(self, title, state_list, island_list)

        # Ensure that current state variable has the most recent information
        self.current_state = state_list[-1]

        # Feed the objective function state list.
        return state_list, island_list

    def action_gen(self, bus_id):

        # Verify that action is available!
        ind = self.action_list['gen'] == bus_id
        if np.sum(ind) != 1:
            print('Load not on action list!')
            return [], []

        # Take preliminary snapshot of the system
        state_list, island_list = take_snapshot(self, 'Preliminary state', [], [])

        # What islands does the bus reside on?
        bus_ind = self.current_state['bus voltage angle'][:, 0] == bus_id
        island = int(self.current_state['bus voltage angle'][bus_ind, 2])

        if island == -1:
            # print('Can not activate generator within blackout area!')
            return [], []

        # Activate the generator
        # I have to be careful to select the generator (a dispatchable load may reside on the same bus)
        gen_ind = np.where(self.octave.isload(self.islands[self.island_map[island]]['gen']) == 0)[0]  # indicies of generators
        bus_ind = np.where(self.islands[self.island_map[island]]['gen'][gen_ind, 0] == bus_id)  # index to gen_ind
        self.islands[self.island_map[island]]['gen'][gen_ind[bus_ind], 7] = 1

        # Evaluate islands with new generator connection
        success = self.evaluate_islands()
        if success == 0:
            return [], []

        # Take snapshot
        title = 'Connecting generator on bus %s' % int(bus_id)
        state_list, island_list = take_snapshot(self, title, state_list, island_list)

        # Ensure that current state variable has the most recent information
        self.current_state = state_list[-1]

        # Feed the objective function state list.
        return state_list, island_list

    def get_losses(self, case):

        # Evaluate system losses
        case['losses'] = np.real(np.sum(self.octave.get_losses(case['baseMVA'], case['bus'], case['branch'])))

        return case

    def is_load_is_gen(self, case_list):

        # Flag if there is gen and or load
        for island in make_iterable(case_list):

            # Does the island have loads?
            if np.all(island['bus'][:, 2:4] == 0) and np.all(self.octave.isload(island['gen']) == 0):  # True for no loads
                island['is_load'] = 0
            else:
                island['is_load'] = 1

            # Are there generators?
            try:
                if np.sum(self.octave.isload(island['gen']) == 0) > 0:
                    island['is_gen'] = 1
                else:
                    # If there are no generators, we can stop here
                    island['is_gen'] = 0
            except:
                island['is_gen'] = 0


        # Reshape case list if it is a oct2py cell
        if type(case_list) == oct2py.io.Cell:
            return case_list.reshape((-1))
        else:
            return case_list

    def set_opf_constraints(self, test_case, set_branch=(), max_spa=365, set_gen=True, set_loads=True):

        # Work with copy of test case
        test_case_opf = deepcopy(test_case)

        if len(set_branch) > 0:
            # Constrain deactivated target branch to max SPA
            test_case_opf['branch'][set_branch, 11:13] = [-max_spa, max_spa]

        if set_loads:  # Look at load2disp for future implementations(converts fixed loads to dispatchable loads)

            # Snapshot of fixed loads, before we set the dispatchable ones to zero
            real_loads = deepcopy(test_case_opf['bus'][:, 2])
            react_loads = deepcopy(test_case_opf['bus'][:, 3])

            # Set dispatchable loads in the bus matrix to zero
            test_case_opf['bus'][self.dispatchable_loads == 1, 2:4] = 0

            # Reshape the gencost matrix so that we can add up to 3 points in piecewise objective function
            test_case_opf['gencost'] = reshape_gencost(test_case_opf['gencost'])

            # Represent dispatchable loads as negative generators!
            for i in range(len(self.dispatchable_loads)):

                # If load is identified as dispatchable
                if self.dispatchable_loads[i]:
                    # Gen setup: BUS, PG, QG, Qmax, Qmin, VG, MBASE, STATUS, PMAX, PMIN
                    new_gen = [test_case_opf['bus'][i, 0],
                               -real_loads[i],
                               -react_loads[i],
                               np.max([0, -react_loads[i]]),
                               np.min([0, -react_loads[i]]),
                               1,
                               test_case_opf['baseMVA'],
                               1,
                               0,
                               -real_loads[i]]
                    filler = len(test_case_opf['gen'][0]) - len(new_gen)
                    new_gen = np.append(new_gen, filler * [0]).reshape((1, -1))

                    # Append dispatchable load to gen matrix
                    if type(test_case_opf['gen']) == list:
                        test_case_opf['gen'] = deepcopy(new_gen)
                    else:
                        test_case_opf['gen'] = np.append(test_case_opf['gen'], new_gen, axis=0)

                    # Append dispatchable load to gencost matrix
                    # [model, startup cost, shutdown cost, data points, parameters (p(MW), f($/hr))]
                    new_gencost = np.array([1, 0, 0, 2, -real_loads[i], -real_loads[i]*self.metadata['dispatch_load_cost'][0], 0, 0, 0, 0]).reshape((1, -1))
                    if test_case_opf['gencost'].size == 0:
                        test_case_opf['gencost'] = deepcopy(new_gencost)
                    else:
                        test_case_opf['gencost'] = np.append(test_case_opf['gencost'], new_gencost, axis=0)

                    # Two endpoints of all gencost functions
                    test_case_opf['gencost'][-1, 3] = 2

        if set_gen:
            # Set objective function of each non-load generator as "V" function around scheduled set point
            # s = test_case_opf['gencost'].shape
            # test_case_opf['gencost'] = np.resize(test_case_opf['gencost'], (s[0], 10))

            # Which generators are real? Only loop over the real ones
            legit_gen = self.octave.isload(test_case_opf['gen'])

            if type(legit_gen) == int:
                legit_gen = [legit_gen, ]

            # print(test_case_opf['gencost'])
            # print(test_case_opf['gencost'].shape)
            for i, gen in enumerate(test_case_opf['gencost']):

                # Only perform on non-load generators
                if legit_gen[i] == 0:
                    # Model type = piecewise linear
                    gen[0] = 1

                    # Find set point and max real power for generator i
                    set_point = test_case_opf['gen'][i][1]
                    max_active = test_case_opf['gen'][i][8]

                    # Cost/minimization model
                    if set_point > 0:
                        # Number of vertices of piecewise model
                        gen[3] = 3
                        # Set "V" objective function around the scheduled set-point.
                        gen[4:] = [0, set_point, set_point, 0, max_active, max_active - set_point]
                    else:
                        # Number of vertices of piecewise model
                        gen[3] = 2
                        # Set "V" objective function around the scheduled set-point.
                        gen[4:] = [0, 0, max_active, max_active, 0, 0]
                else:
                    continue

        return test_case_opf

