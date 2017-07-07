import pypower.api as pp
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

''' 
This is the power system simulation code and visualization framework
'''


# Load PyPower case and run power flow analysis
c6 = pp.loadcase(pp.case9(), return_as_obj=True, expect_gencost=False, expect_areas=False)
results, success = pp.runpf(c6)

# Get result dimensions
n_bra = c6['branch'].shape[0]
n_bus = c6['bus'].shape[0]
n_gen = c6['gen'].shape[0]

# Calculate MVA power injection to each line
MVA_inj = np.sqrt(results['branch'][:, 13]**2 + results['branch'][:, 14]**2)
MVA_rating = results['branch'][:, [5, 6, 7]].min(1)
MVA_ratio = MVA_inj/MVA_rating

# Calculate bus parameters
# V_ratio = (results['bus'][:, 7] - results['bus'][:, 12])/(results['bus'][:, 11] - results['bus'][:, 12])
# V_ratio[np.isnan(V_ratio)] = 0.5

# Develop graph representation of results
G = nx.Graph()

# Add buses as nodes
# ---------------- bus and load data --------------------
# bus_i type Pd Qd Gs Bs area Vm Va baseKV zone Vmax Vmin
for i in range(n_bus):
    # Buses
    params = {'bus': int(results['bus'][i, 0]),
              'V magnitude': results['bus'][i, 7],
              # 'V ratio': V_ratio[i],
              'V angle': results['bus'][i, 8],
              'V mag max': results['bus'][i, 11],
              'V mag min': results['bus'][i, 12],
              'nodecolor': 'w',
              'nodetype': 'bus',
              'nodenumber': i+1}
    G.add_node(i+1, params)

    # Loads
    if results['bus'][i, 2] or results['bus'][i, 3] > 0:
        params = {'bus': int(results['bus'][i, 0]),
                  'Pd': results['bus'][i, 2],
                  'Qd': results['bus'][i, 3],
                  'nodecolor': 'r',
                  'nodetype': 'load',
                  'nodenumber': i + 2001}
        G.add_node(i + 2001, params)

# Add generators and loads as secondary nodes
# ------------- generator data -------------
# bus, Pg, Qg, Qmax, Qmin, Vg, mBase, status, Pmax, Pmin, Pc1, Pc2,
# Qc1min, Qc1max, Qc2min, Qc2max, ramp_agc, ramp_10, ramp_30, ramp_q, apf
for i in range(n_gen):
    params = {'bus': int(results['gen'][i, 0]),
              'Pg': results['gen'][i, 1],
              'Qg': results['gen'][i, 2],
              'Qmax': results['gen'][i, 3],
              'Qmin': results['gen'][i, 4],
              'Pmax': results['gen'][i, 8],
              'Pmin': results['gen'][i, 9],
              'nodecolor': 'g',
              'nodetype': 'generator',
              'nodenumber': i + 1001}
    G.add_node(i+1001, params)

# Add lines, generator connections and load connections
# ---------------- branch data --------------------
# fbus, tbus, r, x, b, rateA, rateB, rateC, ratio, angle, status, angmin, angmax
for i in range(n_bra):
    # TODO: figure out how to add losses of each line (I^2 *Z)
    params = {'MVA_inj': MVA_inj[i],
              'MVA_rating': MVA_rating[i],
              'MVA_ratio': MVA_ratio[i],
              'edgenumber': i,
              'edgetype': 'branch'}
    G.add_edge(results['branch'][i, 0],  results['branch'][i, 1], params)

for i in [node for node in G.node.values() if node['nodetype'] in ['generator', 'load']]:
    params = {'MVA_ratio': 0,
              'edgenumber': i['bus']+1000,
              'edgetype': 'connector'}
    G.add_edge(i['nodenumber'], i['bus'], params)


# Visualize graph
fig = plt.figure(figsize=(12,6))
ax1 = plt.subplot(121)
ax2 = plt.subplot(122)
nx.draw_networkx(G,
                 node_size=500,
                 node_color=[node['nodecolor'] for node in G.node.values()],
                 # cmap='RdBu',
                 # vmin=0,
                 # vmax=1,
                 width=4,
                 edge_color=[edge[2]['MVA_ratio'] for edge in G.edges(data=True)],
                 edge_cmap=plt.get_cmap('Reds'),
                 edge_vmin=0,
                 edge_vmax=1,
                 with_labels=True,
                 pos=nx.spectral_layout(G),
                 ax=ax1)
plt.show()

# TODO: Be thinking of what parameters are control parameters and which ones are optimization parameters

