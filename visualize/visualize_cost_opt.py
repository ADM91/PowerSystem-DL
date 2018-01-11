import matplotlib.pyplot as plt
import numpy as np
import pickle


def visualize_cost_opt(files, legend_names, title, fig_num=1):

    for file, legend_name in zip(files, legend_names):
        with open(file, 'rb') as f:
            data = pickle.load(f)

        color = np.random.rand(3, 1)

        # Find number of optimizations and runs per optimization
        n_opt = len(data.keys())
        n_iter = len(data['opt 0'].keys()) - 3

        # Populate matrix of best total costs
        matrix = np.empty((n_opt, n_iter))
        for i, opt in enumerate(data.values()):
            matrix[i, :] = opt['best_total_cost_store']

        # Plot!
        plt.figure(fig_num)
        for i in range(n_opt):
            plt.plot(matrix[i, :], c=color)
        plt.title(file)

        plt.figure(fig_num + 1)
        plt.plot(np.min(matrix, axis=0), c=color)
        plt.plot(np.max(matrix, axis=0), c=color)
        plt.plot(np.mean(matrix, axis=0), '--', c=color, label=legend_name)
        # plt.legend(['Lower envelope', 'Upper envelope', 'Mean'])

    # Add legend and title
    plt.figure(fig_num + 1)
    plt.legend(loc='best')
    plt.title(title)

    return matrix






