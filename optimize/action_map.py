

def create_action_map(action_list):

    action_map = dict()

    count = 0
    for item in action_list.items():
        if len(item[1]) > 0:
            for value in item[1]:
                action_map[count] = [item[0], value]
                count += 1

    return action_map


