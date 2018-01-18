from anytree import Node, RenderTree
import anytree
import numpy as np
from copy import copy, deepcopy


class RestorationTree:
    def __init__(self):
        self.action_list = []
        self.root = Node('root',
                         state=None,
                         islands=None,
                         actions_remaining=None)

    def fill_root(self, state, islands, action_list):
        n_actions = int(np.sum([len(item) for item in action_list.values()]))
        self.action_list = np.arange(n_actions)
        self.root.state = state
        self.root.islands = islands
        self.root.actions_remaining = np.arange(n_actions)

    def create_nodes(self, parent):

        # Node name: action number
        if len(parent.actions_remaining) > 0:
            for action in parent.actions_remaining:

                action_ind = np.where(parent.actions_remaining == action)
                actions_remaining = np.delete(parent.actions_remaining, action_ind)  # deletes action from list

                new_node = Node('a' + str(action),
                                parent=parent,
                                state=None,
                                islands=None,
                                cost=0,
                                time=[],
                                energy=[],
                                action=action,
                                actions_remaining=actions_remaining)






