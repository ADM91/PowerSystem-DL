from anytree import Node, RenderTree
import numpy as np


class RestorationTree:
    def __init__(self, ps):

        self.ps = ps
        n_actions = int(np.sum([len(item) for item in ps.action_list.values()]))
        self.action_list = np.arange(n_actions)
        self.root = Node('root', actions_remaining=np.arange(n_actions))
        self.queue = [self.root]

    def generate_tree(self):

        # Generate the tree!
        count = 0
        while len(self.queue) > 0:
            parent = self.queue.pop()
            self.create_nodes(parent)
            count += 1
            if count % 5000 == 0:
                print(count, len(self.queue))

    def create_nodes(self, parent):

        # Node name: action number
        if len(parent.actions_remaining) > 0:
            for action in parent.actions_remaining:

                action_ind = np.where(parent.actions_remaining == action)
                actions_remaining = np.delete(parent.actions_remaining, action_ind)  # deletes action from list

                # is action at edge of an energized area?


                new_node = Node('a' + str(action),
                                parent=parent,
                                states=[],
                                cost=0,
                                actions_remaining=actions_remaining,
                                visited=False)
                self.queue.append(new_node)






