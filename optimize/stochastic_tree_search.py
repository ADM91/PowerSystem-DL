from auxiliary.open_path import safe_open_w
import pickle
from optimize.action_map import create_action_map
from objective.objective_function import objective_function
import numpy as np
from copy import deepcopy
from anytree import Walker

w = Walker()


def stochastic_tree_search(ps, tree, opt_iteration, verbose=1, save_data=0, folder='test'):

    # Reset data storage
    states_store = []
    time_store = []
    energy_store = []
    restoration_cost_store = []
    sequence_store = []
    best_total_cost = []

    # Creates a dictionary of integer - action pairs
    action_map = create_action_map(ps.action_list)

    # Cheapest restoration:
    cheapest = 99999
    for i in range(opt_iteration):

        # Set parent as root
        par = tree.root

        if verbose:
            print('\niteration: %s' % i)

        # while loop: while we have not exhausted action set
        while len(par.actions_remaining) > 0:

            if verbose:
                print('actions remaining: %s' % len(par.actions_remaining))

            # Create children if they don't exist
            if par.is_leaf:

                # Creates the children
                tree.create_nodes(par)

                # Evaluate power system at each child
                for child in par.children:

                    if verbose:
                        print('testing child: %s' % child.name)
                        print('action to perform: %s' % action_map[child.action][0])
                        print('buse(s) involved: %s' % action_map[child.action][1])

                    action = action_map[child.action]

                    # Evaluate action (make sure I can revert the action)
                    if action[0] == 'line':
                        output = ps.action_line(action[1])
                    elif action[0] == 'fixed load':
                        output = ps.action_fixed_load(action[1])
                    elif action[0] == 'dispatch load':
                        output = ps.action_dispatch_load(action[1])
                    elif action[0] == 'gen':
                        output = ps.action_gen(action[1])
                    else:
                        print('Action string not recognized')

                    # Evaluate cost function and update child
                    if len(output) > 0:
                        [restore_time, energy, cost] = objective_function(output, ps.ideal_state)
                        child.cost = cost['combined total']
                        child.state = deepcopy(ps.current_state)
                        child.islands = deepcopy(ps.islands)
                        if verbose:
                            print('Action success')

                    else:
                        # remove leaf consisting of invalid action
                        child.parent = None
                        if verbose:
                            print('Action failure')

                    # Revert to parent state so we can test next child
                    ps.revert(par.islands, par.state, {'buses': [], 'lines': []})  # deprecating the blackout connection dictionary

            # Choose next parent stochastically!
            # If no valid children exist:
            if par.is_leaf:
                # Pick a sibling as new parent!
                cost_store = np.array([sib.cost for sib in par.siblings])
                siblings_store = [sib for sib in par.siblings]

                # Remove the parent with bastard children
                par.parent = None

                # Select a sibling of the shitty parent
                probabilities = (1 / cost_store) / np.sum(1 / cost_store)
                par = np.random.choice(siblings_store, p=probabilities)

                if verbose:
                    print('All children failed, selecting sibiling: %s' % par.name)

            # If we have valid children:
            else:
                cost_store = np.array([child.cost for child in par.children])
                child_store = [child for child in par.children]
                probabilities = (1/cost_store)/np.sum(1/cost_store)
                if verbose:
                    print('candidate children : %s' % [child.name for child in child_store])
                    print('candidate costs: %s' % cost_store)
                    print('candidate probabilities: %s' % probabilities)
                par = np.random.choice(child_store, p=probabilities)
                if verbose:
                    print('Child selected: %s' % par.name)


            # Revert power system to chosen parent!
            ps.revert(par.islands, par.state, {'buses': [], 'lines': []})

        # Evaluate the restoration!!!
        # Need to trace root to current parent (should be leaf) collect sequence and cost.
        if par.is_leaf:
            seq = w.walk(tree.root, par)
            # print(seq)
            total_cost = np.sum([node.cost for node in seq[-1]])
            action_seq = [node.action for node in seq[-1]]
            print(action_seq)
            restoration_cost_store.append(total_cost)
            sequence_store.append(action_seq)
            if total_cost < cheapest:
                best_total_cost.append(total_cost)
                cheapest = total_cost
            else:
                best_total_cost.append(cheapest)
        else:
            print('Last node in run is somehow not a leaf node??!?!?!?!?')

    # Save data to pickle
    if save_data:
        data = [restoration_cost_store, sequence_store, best_total_cost]
        with safe_open_w("data/%s/stochastic_opt_%s.pickle" % (folder, i), 'wb') as output_file:
            pickle.dump(data, output_file)

    return [restoration_cost_store, sequence_store, best_total_cost, seq]
