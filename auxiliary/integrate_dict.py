from auxiliary.iterable import iterable


def integrate_dict(dict1, dict2):

    # Combines the contents of two similar dictionaries
    for key in dict1.keys():
        if key in dict2.keys():
            for item in iterable(dict2[key]):
                dict1[key].append(item)
        else:
            print('Error: dictionary keys do not match!!!')

    return dict1
