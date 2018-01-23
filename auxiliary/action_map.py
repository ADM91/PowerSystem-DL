

def create_action_map(action_list):
    # takes power system action list dictionary and creates an action map dictionary where the keys are integers

    action_map = dict()

    count = 0
    for item in action_list.items():
        if len(item[1]) > 0:
            for value in item[1]:
                action_map[count] = [item[0], value]
                count += 1

    return action_map


