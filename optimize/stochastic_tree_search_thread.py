from objective.objective_function import objective_function
from copy import deepcopy
import numpy as np
from auxiliary.integrate_dict import integrate_dict
from anytree import Walker


# -------------------------------------
# Multi-thread each restoration iteration (is useful for both tree and genetic)
# -------------------------------------

def stochastic_tree_search_thread(stuff):

    # Unpack all the variables
    [i, ii,
     ps,
     tree,
     data, total_cost_store, best_total_cost_store, action_sequence_store, cheapest,
     lock,
     method,
     action_map,
     verbose] = stuff

    w = Walker()

    # Restoration simulation run dictionary
    with lock:
        data['opt %s' % i]['run %s' % ii] = {}

    # Set parent as root
    par = tree.root

    if verbose:
        print('\noptimization: %s' % i)
        print('iteration: %s' % ii)

    # while loop: while we have not exhausted action set
    while len(par.actions_remaining) > 0:

        if verbose:
            print('actions remaining: %s' % len(par.actions_remaining))

        # Create children if they don't exist
        if par.is_leaf:

            # Creates the children
            with lock:
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
                    state_list, island_list = ps.action_line(action[1])
                elif action[0] == 'fixed load':
                    state_list, island_list = ps.action_fixed_load(action[1])
                elif action[0] == 'dispatch load':
                    state_list, island_list = ps.action_dispatch_load(action[1])
                elif action[0] == 'gen':
                    state_list, island_list = ps.action_gen(action[1])
                else:
                    print('Action string not recognized')

                # Evaluate cost function and update child
                if len(state_list) > 0:
                    [restore_time, energy, cost] = objective_function(state_list, ps.ideal_state)
                    with lock:  # TODO: do I need a lock here? i am writing to the tree object
                        child.cost = cost
                        child.time = restore_time
                        child.energy = energy
                        child.state = deepcopy(ps.current_state)
                        child.islands = deepcopy(ps.islands)

                    if verbose:
                        print('Action success')

                else:
                    # remove leaf consisting of invalid action
                    with lock:
                        child.parent = None
                    if verbose:
                        print('Action failure')

                # Revert to parent state so we can test next child
                ps.revert(deepcopy(par.state), deepcopy(par.islands))  # deprecating the blackout connection dictionary

        # Choose next parent stochastically!
        # If no valid children exist:
        if par.is_leaf:
            # Pick a sibling as new parent!
            cost_store = np.array([sib.cost['combined total'] for sib in par.siblings])
            siblings_store = [sib for sib in par.siblings]

            # Remove the parent with bastard children
            with lock:
                par.parent = None

            # Select a sibling of the shitty parent
            if method == 'cost':
                probabilities = (1 / cost_store) / np.sum(1 / cost_store)
            elif method == 'inverse cost':
                probabilities = cost_store / np.sum(cost_store)
            elif method == 'rank':
                temp = cost_store.argsort()
                rank = np.empty_like(temp)
                rank[temp] = np.arange(len(cost_store))
                probabilities = (1 / (rank + 1)) / np.sum(1 / (rank + 1))
            elif method == 'uniform':
                probabilities = np.ones(cost_store.shape) / len(cost_store)
            elif method == 'inverse rank':
                temp = cost_store.argsort()
                rank = np.empty_like(temp)
                rank[temp] = np.arange(len(cost_store))
                probabilities = (rank + 1) / np.sum(rank + 1)
            else:
                print('Unrecognized method')
                return

            par = np.random.choice(siblings_store, p=probabilities)

            if verbose:
                print('All children failed, selecting sibiling: %s' % par.name)

        # If we have valid children:
        else:
            child_store = [child for child in par.children]
            cost_store = np.array([child.cost['combined total'] for child in child_store])

            if method == 'cost':
                probabilities = (1 / cost_store) / np.sum(1 / cost_store)
            elif method == 'inverse cost':
                probabilities = cost_store / np.sum(cost_store)
            elif method == 'rank':
                temp = cost_store.argsort()
                rank = np.empty_like(temp)
                rank[temp] = np.arange(len(cost_store))
                probabilities = (1 / (rank + 1)) / np.sum(1 / (rank + 1))
            elif method == 'uniform':
                probabilities = np.ones(cost_store.shape) / len(cost_store)
            elif method == 'inverse rank':
                temp = cost_store.argsort()
                rank = np.empty_like(temp)
                rank[temp] = np.arange(len(cost_store))
                probabilities = (rank + 1) / np.sum(rank + 1)
            else:
                print('Unrecognized method')
                return

            if verbose:
                print('candidate children : %s' % [child.name for child in child_store])
                print('candidate costs: %s' % cost_store)
                print('candidate probabilities: %s' % probabilities)

            par = np.random.choice(child_store, p=probabilities)
            if verbose:
                print('Child selected: %s' % par.name)

        # Revert power system to chosen child or sibling!
        ps.revert(deepcopy(par.state), deepcopy(par.islands))

    # Evaluate the restoration!!!
    # Need to trace root to current parent (should be leaf) collect sequence and cost.
    energy_store = {'lost load': [],
                    'losses': [],
                    'dispatch deviation': []}
    cost_store = {'lost load': [],
                  'losses': [],
                  'dispatch deviation': [],
                  'total': [],
                  'combined total': []}
    time_store = []
    action_seq = []

    if par.is_leaf:

        # Collect the nodes from root to the newest leaf
        # TODO: do I need a lock for this?
        seq = w.walk(tree.root, par)[-1]

        # Collect data from each node
        for node in seq:
            action_seq.append(node.action)
            cost_store = integrate_dict(cost_store, node.cost)
            energy_store = integrate_dict(energy_store, node.energy)
            for time in node.time:
                time_store.append(time)
        cost_store['combined total'] = np.sum(cost_store['combined total'])

        # Place data in the data dictionary
        data['opt %s' % i]['run %s' % ii]['cost'] = deepcopy(cost_store)
        data['opt %s' % i]['run %s' % ii]['energy'] = deepcopy(energy_store)
        data['opt %s' % i]['run %s' % ii]['time'] = deepcopy(time_store)
        data['opt %s' % i]['run %s' % ii]['sequence'] = deepcopy(action_seq)

        # Append to the optimization data lists
        total_cost_store.append(deepcopy(cost_store['combined total']))
        action_sequence_store.append(action_seq)
        if cost_store['combined total'] < cheapest:
            best_total_cost_store.append(deepcopy(cost_store['combined total']))
            cheapest = deepcopy(cost_store['combined total'])
        else:
            best_total_cost_store.append(cheapest)

    else:
        print('Last node in run is somehow not a leaf node??!?!?!?!?')
