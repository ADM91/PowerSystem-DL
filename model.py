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

# Develop graph representation of results
G = nx.Graph()
# Add buses as nodes
for i in range(n_bus):
    params = {'V magnitude': results['bus'][i, 7],
              'V angle': results['bus'][i, 8],
              'V mag max': results['bus'][i, 11],
              'V mag min': results['bus'][i, 12]}
    G.add_node(i, params)

# Add branches as edges
for i in range(n_bra):
    params = {'V magnitude': results['bus'][i, 7],
              'V angle': results['bus'][i, 8],
              'V mag max': results['bus'][i, 11],
              'V mag min': results['bus'][i, 12]}
    G.add_edge(results['bus'][i, 0],  results['bus'][i, 1], params)

# Visualize graph
nx.draw(G)
plt.show()



