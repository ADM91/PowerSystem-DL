import matplotlib.pyplot as plt
import numpy as np


def visualize_cost(time, cost, fig_num=1):

    # Visualize energy lost
    t = np.cumsum(time)
    y1 = np.cumsum(cost['dispatch deviation'])
    y2 = np.cumsum(cost['losses'])
    y3 = np.cumsum(cost['lost load'])

    plt.figure(fig_num)
    plt.grid()
    plt.plot(t, y1, 'b-')
    plt.plot(t, y2, 'r-')
    plt.plot(t, y3, 'g-')
    plt.xlabel('time (min)')
    plt.ylabel('cumulative objective')
