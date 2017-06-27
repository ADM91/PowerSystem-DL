import numpy as np
import tensorflow as tf
import scipy as sp
import sklearn as skl
import pandas as pd
import pypower.api as pp
import networkx as nx
import matplotlib.pyplot as plt

# Load pypower case and run power flow analysis
c6 = pp.loadcase(pp.case6ww(), return_as_obj=True, expect_gencost=False, expect_areas=False)
result = pp.runpf(c6)

# Develop some graph visualization stuff
G = nx.Graph()
G.add_node(1, {'size': 10, 'color': 'b'})
G.add_node(2, {'size': 5, 'color': 'g'})
G.add_node(3, {'size': 13, 'color': 'r'})
G.add_edge(1, 2, {'length': 2})
G.add_edge(1, 3, {'length': 1})
G.add_edge(2, 3, {'length': 3})

nx.draw(G)
plt.show()



