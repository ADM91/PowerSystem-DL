import matplotlib.pyplot as plt
import numpy as np


def visualize_cost_ga(matrix, title):

    color = np.random.rand(3, 1)

    plt.figure()
    plt.plot(np.min(matrix, axis=1), c=color)
    plt.plot(np.max(matrix, axis=1), c=color)
    plt.plot(np.mean(matrix, axis=1), '--', c=color)
    # plt.legend(['Lower envelope', 'Upper envelope', 'Mean'])

    # Add legend and title
    plt.title(title)
