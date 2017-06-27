import pypower.api as pp
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# Load PyPower case and run power flow analysis
c6 = pp.loadcase(pp.case6ww(), return_as_obj=True, expect_gencost=False, expect_areas=False)
results, success = pp.runpf(c6)
n_bra = c6['branch'].shape[0]
n_bus = c6['bus'].shape[0]
n_gen = c6['gen'].shape[0]

# Calculate MVA power injection to each line
MVA_inj = np.sqrt(results['branch'][:, 13]**2 + results['branch'][:, 14]**2)
MVA_rating = results['branch'][:, [5, 6, 7]].min(1)
MVA_ratio = MVA_inj/MVA_rating
V_ratio = (results['bus'][:, 7] - results['bus'][:, 12])/(results['bus'][:, 11] - results['bus'][:, 12])
V_ratio[np.isnan(V_ratio)] = 0.5

# Develop graph representation of results
G = nx.Graph()
# Add buses as nodes
for i in range(n_bus):
    # TODO: Add generation and loads
    params = {'V magnitude': results['bus'][i, 7],
              'V ratio': V_ratio[i],
              'V angle': results['bus'][i, 8],
              'V mag max': results['bus'][i, 11],
              'V mag min': results['bus'][i, 12]}
    G.add_node(i, params)

# Add branches as edges
for i in range(n_bra):
    # TODO: figure out how to add losses of each line
    params = {'MVA_inj': MVA_inj[i],
              'MVA_rating': MVA_rating[i],
              'MVA_ratio': MVA_ratio[i]}
    G.add_edge(results['branch'][i, 0]-1,  results['branch'][i, 1]-1, params)

# Visualize graph
nx.draw_networkx(G,
                 node_size=500,
                 node_color=V_ratio,
                 cmap='RdBu',
                 vmin=0,
                 vmax=1,
                 width=4,
                 edge_color=MVA_ratio,
                 edge_cmap=plt.get_cmap('Reds'),
                 edge_vmin=0,
                 edge_vmax=1,
                 with_labels=True)
plt.show()

# TODO: Be thinking of what parameters are control parameters and which ones are optimization parameters

