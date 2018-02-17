import matplotlib.pyplot as plt
import numpy as np
import pickle
from glob import glob


def visualize_cost_opt_ga(folder, title):

    files = glob(folder + '/*')

    for i, file in enumerate(files):
        with open(file, 'rb') as f:
            data = pickle.load(f)

        color = np.random.rand(3, 1)

        # Find number of optimizations and runs per optimization
        # n_opt = len(data.keys())
        # n_iter = len(data.keys()) - 3

        min_line = np.min(data['total_cost_store'], axis=1)
        max_line = np.max(data['total_cost_store'], axis=1)
        mean_line = np.mean(data['total_cost_store'], axis=1)

        # Plot all min lines on fig 1
        plt.figure(0)
        plt.plot(min_line, c=color)
        plt.title('Lower envelope of every optimization')

        plt.figure(i + 1)
        plt.plot(min_line, c=color)
        plt.plot(max_line, c=color)
        plt.plot(mean_line, '--', c=color, label='mean')
        plt.title('Fitness envelope of optimization %s' % i)

        print('fittest: %s' % data['action_sequence_store'][-1])







