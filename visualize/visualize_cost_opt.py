import matplotlib.pyplot as plt
import numpy as np
import pickle


def visualize_cost_opt(file, fig_num=1):

    with open(file, 'rb') as f:
        data = pickle.load(f)

    # Find number of optimizations and runs per optimization
    n_opt = len(data.keys())
    n_iter = len(data['opt 0'].keys()) - 3

    # Populate matrix of best total costs
    matrix = np.empty((n_opt, n_iter))
    for i, opt in enumerate(data.values()):
        matrix[i, :] = opt['best_total_cost_store']

    # Plot!
    plt.figure(1)
    for i in range(n_opt):
        plt.plot(matrix[i, :])

    plt.figure(2)
    plt.plot(np.min(matrix, axis=0))
    plt.plot(np.max(matrix, axis=0))
    plt.plot(np.mean(matrix, axis=0), '--')
    plt.legend(['Lower envelope', 'Upper envelope', 'Mean'])

    return matrix






