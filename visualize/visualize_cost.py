import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from auxiliary.add_energy import add_energy


def fill_zeros_with_last(arr):
    prev = np.arange(len(arr))
    prev[arr == 0] = 0
    prev = np.maximum.accumulate(prev)
    return arr[prev]


def visualize_cost(time_store, cost, energy, gen_dev, load_dev, loss_dev, fig_num=1):

    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    sns.set_palette("Set1")
    cp = sns.color_palette()

    # Visualize energy lost
    time = np.insert(time_store, 0, [0])
    t = np.cumsum(time)
    y1 = np.cumsum(cost['dispatch deviation'])
    y1 = np.insert(y1, 0, [0])
    y2 = np.cumsum(cost['losses'])
    y2 = np.insert(y2, 0, [0])
    y3 = np.cumsum(cost['lost load'])
    y3 = np.insert(y3, 0, [0])

    # -------------------- Figure 1 -----------------------

    plt.figure(fig_num)
    plt.subplot(211)
    plt.grid()
    plt.plot(t, y1, 'b-', linewidth=2, label='Generator dispatch deviation')
    # plt.plot(t, y2, 'r-', linewidth=2, label='Loss deviation')
    plt.plot(t, y3, 'g-', linewidth=2, label='Load not served')
    plt.title('Cumulative cost over time')
    # plt.xlabel('time (min)')
    plt.ylabel('cumulative cost')
    plt.xlim([0, t[-1]])
    plt.legend(loc=2)

    c = 1
    last = 0
    for i in range(1, len(t)):
        if t[i] == t[i-1]:
            plt.axvline(x=t[i], c='black')
            plt.text(x=last + (t[i] - last)/2 - 0.1, y=300, s='%d' % c)
            c += 1
            last = t[i]
    plt.text(x=last + (t[i] - last) / 2 - 0.1, y=300, s='%d' % c)

    # plt.figure(fig_num+1)
    plt.subplot(212)
    plt.grid()
    plt.plot(t, gen_dev, 'b-', linewidth=2, label='Generator dispatch deviation')
    # plt.plot(t, loss_dev, 'r-', linewidth=2, label='Loss deviation')
    plt.plot(t, load_dev, 'g-', linewidth=2, label='Load not served')
    plt.title('Power deviation over time')
    plt.xlabel('time (min)')
    plt.ylabel('Power (MW)')
    plt.xlim([0, t[-1]])
    plt.legend(loc=0)

    c = 1
    last = 0
    for i in range(1, len(t)):
        if t[i] == t[i-1]:
            plt.axvline(x=t[i], c='black')
            plt.text(x=last + (t[i] - last)/2 - 0.1, y=40, s='%d' % c)
            c += 1
            last = t[i]
    plt.text(x=last + (t[i] - last) / 2 - 0.1, y=40, s='%d' % c)

    # -------------------- Figure 2 -----------------------

    plt.figure(fig_num+1)
    plt.subplot(211)
    plt.grid()
    # plt.plot(t, y1, 'b-', linewidth=2, label='Generator dispatch deviation')
    plt.plot(t, y2, 'r-', linewidth=2, label='Loss deviation')
    # plt.plot(t, y3, 'g-', linewidth=2, label='Load not served')
    plt.title('Cumulative cost over time')
    # plt.xlabel('time (min)')
    plt.ylabel('cumulative cost')
    plt.xlim([0, t[-1]])
    plt.legend(loc=2)

    c = 1
    last = 0
    for i in range(1, len(t)):
        if t[i] == t[i - 1]:
            plt.axvline(x=t[i], c='black')
            plt.text(x=last + (t[i] - last) / 2 - 0.1, y=0, s='%d' % c)
            c += 1
            last = t[i]
    plt.text(x=last + (t[i] - last) / 2 - 0.1, y=0, s='%d' % c)

    # plt.figure(fig_num+1)
    plt.subplot(212)
    plt.grid()
    # plt.plot(t, gen_dev, 'b-', linewidth=2, label='Generator dispatch deviation')
    plt.plot(t, loss_dev, 'r-', linewidth=2, label='Loss deviation')
    # plt.plot(t, load_dev, 'g-', linewidth=2, label='Load not served')
    plt.title('Loss deviation over time')
    plt.xlabel('time (min)')
    plt.ylabel('Power (MW)')
    plt.xlim([0, t[-1]])
    plt.legend(loc=0)

    c = 1
    last = 0
    for i in range(1, len(t)):
        if t[i] == t[i - 1]:
            plt.axvline(x=t[i], c='black')
            plt.text(x=last + (t[i] - last) / 2 - 0.1, y=0, s='%d' % c)
            c += 1
            last = t[i]
    plt.text(x=last + (t[i] - last) / 2 - 0.1, y=0, s='%d' % c)





