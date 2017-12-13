from auxiliary.open_path import safe_open_w
import pickle


def stochastic_tree_search(ps, tree, opt_iteration, verbose=1, save_data=0, folder='test'):

    # Reset data storage
    states_store = []
    time_store = []
    energy_store = []
    cost_store = []
    sequence_store = []

    parent = tree.root

    for i in range(opt_iteration):

        # While actions exist:

        # Create leaves
        tree.create_nodes(parent)

        # Evaluate power system at each leaf,
        for leaf in tree.root.leaves:
            # Evaluate
            # remove leaves that are not valid actions
            pass

        # Use the cost of each evaluation to stochastically choose next action.

        # Set parent as the chosen path

    # Save data to pickle
    if save_data:
        data = [states_store, time_store, energy_store, cost_store, sequence_store, best_total_cost]
        with safe_open_w("data/%s/rand_opt_%s.pickle" % (folder, i), 'wb') as output_file:
            pickle.dump(data, output_file)
