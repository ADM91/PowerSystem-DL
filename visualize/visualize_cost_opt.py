import matplotlib.pyplot as plt
import glob
import pickle


def visualize_cost_opt(folder, title, fig_num=1):

    files = glob.glob('data/%s/*' % folder)

    plt.figure(fig_num)
    plt.grid()
    plt.xlabel('Iteration')
    plt.ylabel('Cost of best performer')
    plt.title(title)

    # Read data from folder
    for file in files:
        with open(file, 'rb') as f:
            data = pickle.load(f)

        # Best performance over iterations
        plt.plot(data[-1][1:50])



