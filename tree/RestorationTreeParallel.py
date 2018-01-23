from anytree import Node
import numpy as np
# from multiprocessing import Lock
# from multiprocessing.managers import BaseManager
from threading import Lock


def create_shared_root(state, islands, action_list):
    n_actions = int(np.sum([len(item) for item in action_list.values()]))
    state = state
    islands = islands
    actions_remaining = np.arange(n_actions)

    # man = BaseManager()
    # man.register('Node', Node, exposed=('name', 'lock', 'state', 'islands', 'actions_remaining'))
    # man.start()

    root = Node('root',
                lock=Lock(),
                state=state,
                islands=islands,
                actions_remaining=actions_remaining)
    return root


def create_children(parent):

    if len(parent.actions_remaining) > 0:
        for action in parent.actions_remaining:
            action_ind = np.where(parent.actions_remaining == action)
            actions_remaining = np.delete(parent.actions_remaining, action_ind)  # deletes action from list

            Node('a' + str(action),
                 parent=parent,
                 lock=Lock(),
                 state=None,
                 islands=None,
                 cost=0,
                 time=[],
                 energy=[],
                 action=action,
                 actions_remaining=actions_remaining)



class RestorationTreeParallel:
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
