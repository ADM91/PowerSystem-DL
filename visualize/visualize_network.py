import networkx as nx
import matplotlib.pyplot as plt
import numpy as np


def visualize_network(case_result):

    # Get result dimensions
    n_bra = case_result['branch'].shape[0]
    n_bus = case_result['bus'].shape[0]
    n_gen = case_result['gen'].shape[0]

    # Calculate MVA power injection to each line
    MVA_inj = np.sqrt(case_result['branch'][:, 13] ** 2 + case_result['branch'][:, 14] ** 2)
    MVA_rating = case_result['branch'][:, 5]
    MVA_ratio = MVA_inj / MVA_rating

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
        params = {'bus': int(case_result['bus'][i, 0]),
                  'V magnitude': case_result['bus'][i, 7],
                  # 'V ratio': V_ratio[i],
                  'V angle': case_result['bus'][i, 8],
                  'V mag max': case_result['bus'][i, 11],
                  'V mag min': case_result['bus'][i, 12],
                  'nodecolor': 'w',
                  'nodetype': 'bus',
                  'nodenumber': i + 1}
        G.add_node(i + 1, params)

        # Loads
        if case_result['bus'][i, 2] or case_result['bus'][i, 3] > 0:
            params = {'bus': int(case_result['bus'][i, 0]),
                      'Pd': case_result['bus'][i, 2],
                      'Qd': case_result['bus'][i, 3],
                      'nodecolor': 'r',
                      'nodetype': 'load',
                      'nodenumber': i + 2001}
            G.add_node(i + 2001, params)

    # Add generators and loads as secondary nodes
    # ------------- generator data -------------
    # bus, Pg, Qg, Qmax, Qmin, Vg, mBase, status, Pmax, Pmin, Pc1, Pc2,
    # Qc1min, Qc1max, Qc2min, Qc2max, ramp_agc, ramp_10, ramp_30, ramp_q, apf
    for i in range(n_gen):
        params = {'bus': int(case_result['gen'][i, 0]),
                  'Pg': case_result['gen'][i, 1],
                  'Qg': case_result['gen'][i, 2],
                  'Qmax': case_result['gen'][i, 3],
                  'Qmin': case_result['gen'][i, 4],
                  'Pmax': case_result['gen'][i, 8],
                  'Pmin': case_result['gen'][i, 9],
                  'nodecolor': 'g',
                  'nodetype': 'generator',
                  'nodenumber': i + 1001}
        G.add_node(i + 1001, params)

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
        G.add_edge(case_result['branch'][i, 0], case_result['branch'][i, 1], params)

    for i in [node for node in G.node.values() if node['nodetype'] in ['generator', 'load']]:
        params = {'MVA_ratio': 0,
                  'edgenumber': i['bus'] + 1000,
                  'edgetype': 'connector'}
        G.add_edge(i['nodenumber'], i['bus'], params)

    # Visualize graph
    plt.figure(2, figsize=(12, 6))
    ax1 = plt.subplot(111)
    # ax2 = plt.subplot(122)
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
