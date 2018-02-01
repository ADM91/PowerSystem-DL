
def generate_dict(iterations, pop_size):

    # Pre-generate data dictionary
    data = dict()
    data['action_sequence_store'] = []
    data['total_cost_store'] = []
    data['best_total_cost_store'] = []
    for iteration in range(iterations):
        data['iter %s' % iteration] = {}
        for indiv in range(pop_size):
            data['iter %s' % iteration]['indiv %s' % indiv] = {}
            data['iter %s' % iteration]['indiv %s' % indiv]['cost'] = []
            data['iter %s' % iteration]['indiv %s' % indiv]['energy'] = []
            data['iter %s' % iteration]['indiv %s' % indiv]['time'] = []
            data['iter %s' % iteration]['indiv %s' % indiv]['sequence'] = []

    return data
