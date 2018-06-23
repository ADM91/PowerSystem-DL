import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from auxiliary.add_energy import add_energy


def fill_zeros_with_last(arr):
    prev = np.arange(len(arr))
    prev[arr == 0] = 0
    prev = np.maximum.accumulate(prev)
    return arr[prev]


def remove_double_zeros(arg):
    rem = []
    last_zero = 0
    for i, item in enumerate(arg):
        if item == 0:
            if last_zero == 1:
                rem.append(i)
            last_zero = 1
        else:
            last_zero = 0

    arg = np.delete(arg, rem)
    return arg, rem


def visualize_cost_by_element(time_store, cost, gen_dev_el, load_dev_el, loss_dev_el, ideal_state, fig_num=1):

    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    sns.set_palette("Set1")
    cp = sns.color_palette()

    # Visualize energy lost
    time, rem = remove_double_zeros(np.insert(time_store, 0, [0]))
    t = np.cumsum(time)
    y1 = np.cumsum(remove_double_zeros(cost['dispatch deviation'])[0])
    y1 = np.insert(y1, 0, [0])
    y2 = np.cumsum(remove_double_zeros(cost['losses'])[0])
    y2 = np.insert(y2, 0, [0])
    y3 = np.cumsum(remove_double_zeros(cost['lost load'])[0])
    y3 = np.insert(y3, 0, [0])

    gen_dev_el = np.delete(gen_dev_el, np.array(rem), axis=0)
    load_dev_el = np.delete(load_dev_el, np.array(rem), axis=0)
    loss_dev_el = np.delete(loss_dev_el, np.array(rem), axis=0)

    # -------------------- Figure 4: Gen-Load dev -----------------------

    fig = plt.figure(6, figsize=(7,8))
    plt.subplot(411)
    plt.grid(axis='y')
    plt.plot(t, y3, 'b-', linewidth=2, label='Unserved load')
    plt.plot(t, y1, 'g-', linewidth=2, label='Generator deviation')
    plt.plot(t, y2, 'r-', linewidth=2, label='Losses')
    plt.title('Cumulative costs')
    plt.ylabel('cumulative cost')
    plt.xlim([0, t[-1]])
    # plt.ylim(bottom=0)
    plt.legend(loc=2)

    c = 1
    last = 0
    for i in range(1, len(t)):
        if t[i] == t[i-1]:
            plt.axvline(x=t[i], c='black')
            plt.text(x=last + (t[i] - last)/2 - 0.1, y=5000, s='%d' % c)
            c += 1
            last = t[i]
    # plt.text(x=last + (t[i] - last) / 2 - 0.1, y=50, s='%d' % c)

    # Unerserved load
    labels = np.concatenate((ideal_state['fixed load'][:, 0], ideal_state['dispatch load'][:, 0]))
    labels = labels[sum(load_dev_el) > 0.01]
    labels = np.array(['bus %d' % l for l in labels])
    load_dev_el = load_dev_el[:, sum(load_dev_el) > 0.01]
    load_dev_el = load_dev_el[:, np.argsort(load_dev_el[0])]
    labels = labels[np.argsort(load_dev_el[0])]
    # labels = ['bus 3','bus 4','bus 8','bus 2',]

    plt.subplot(412)
    plt.grid(axis='y')
    plt.stackplot(t, load_dev_el.T, baseline='zero', labels=labels)
    plt.title('Unserved load by bus')
    # plt.xlabel('time (min)')
    plt.ylabel('Power (MW)')
    plt.xlim([0, t[-1]])
    plt.legend(loc=1)
    plt.tight_layout()

    c = 1
    last = 0
    for i in range(1, len(t)):
        if t[i] == t[i-1]:
            plt.axvline(x=t[i], c='black')
            # plt.text(x=last + (t[i] - last)/2 - 0.1, y=30, s='%d' % c)
            c += 1
            last = t[i]

    # Generator deviation
    labels = ideal_state['real gen'][:, 0]
    labels = np.array(['bus %d' % l for l in labels])
    labels = labels[np.where(np.sum(gen_dev_el, axis=0) > 1)[0]]
    # Cut the low deviation generators out, order by deviation
    gen_dev_el = gen_dev_el[:, np.where(np.sum(gen_dev_el, axis=0) > 1)[0]]
    labels = labels[np.argsort(gen_dev_el[0])]
    gen_dev_el = gen_dev_el[:, np.argsort(gen_dev_el[0])]
    plt.subplot(413)
    plt.grid(axis='y')
    plt.stackplot(t, gen_dev_el.T, baseline='zero', labels=labels)
    plt.title('Power deviation by generator')
    # plt.xlabel('time (min)')
    plt.ylabel('Power (MW)')
    plt.xlim([0, t[-1]])
    plt.legend(loc=1)
    plt.tight_layout()

    c = 1
    last = 0
    for i in range(1, len(t)):
        if t[i] == t[i-1]:
            plt.axvline(x=t[i], c='black')
            # plt.text(x=last + (t[i] - last)/2 - 0.1, y=40, s='%d' % c)
            c += 1
            last = t[i]

    # Losses
    plt.subplot(414)
    plt.grid(axis='y')
    # plt.plot(t, gen_dev, 'b-', linewidth=2, label='Generator dispatch deviation')
    plt.plot(t, loss_dev_el, 'r-', linewidth=2)
    # plt.plot(t, load_dev, 'g-', linewidth=2, label='Load not served')
    plt.title('System loss deviation')
    plt.xlabel('time (min)')
    plt.ylabel('Power (MW)')
    plt.xlim([0, t[-1]])
    plt.tight_layout()
    # plt.legend(loc=0)

    c = 1
    last = 0
    for i in range(1, len(t)):
        if t[i] == t[i - 1]:
            plt.axvline(x=t[i], c='black')
            # plt.text(x=last + (t[i] - last) / 2 - 0.1, y=0, s='%d' % c)
            c += 1
            last = t[i]

    plt.tight_layout()
    fig.savefig('dev_cost.pdf', bbox_inches='tight')



    # -------------------- Figure 1: Gen dev -----------------------

    # plt.figure(3)
    # plt.subplot(211)
    # plt.grid(axis='y')
    # plt.plot(t, y1, 'b-', linewidth=2)
    # plt.title('Cumulative cost due to generator deviation')
    # plt.ylabel('cumulative cost')
    # plt.xlim([0, t[-1]])
    # plt.ylim(bottom=0)
    # # plt.legend(loc=2)
    #
    # c = 1
    # last = 0
    # for i in range(1, len(t)):
    #     if t[i] == t[i-1]:
    #         plt.axvline(x=t[i], c='black')
    #         plt.text(x=last + (t[i] - last)/2 - 0.1, y=50, s='%d' % c)
    #         c += 1
    #         last = t[i]
    # # plt.text(x=last + (t[i] - last) / 2 - 0.1, y=50, s='%d' % c)
    #
    # labels = ideal_state['real gen'][:, 0]
    # labels = np.array(['bus %d' % l for l in labels])
    # labels = labels[np.where(np.sum(gen_dev_el, axis=0) > 1)[0]]
    # # Cut the low deviation generators out, order by deviation
    # gen_dev_el = gen_dev_el[:, np.where(np.sum(gen_dev_el, axis=0) > 1)[0]]
    # gen_dev_el = gen_dev_el[:, np.argsort(gen_dev_el[0])]
    # plt.subplot(212)
    # plt.grid(axis='y')
    # plt.stackplot(t, gen_dev_el.T, baseline='zero', labels=labels)
    # plt.title('Power deviation by generator')
    # plt.xlabel('time (min)')
    # plt.ylabel('Power (MW)')
    # plt.xlim([0, t[-1]])
    # plt.legend(loc=1)
    # plt.tight_layout()
    #
    # c = 1
    # last = 0
    # for i in range(1, len(t)):
    #     if t[i] == t[i-1]:
    #         plt.axvline(x=t[i], c='black')
    #         # plt.text(x=last + (t[i] - last)/2 - 0.1, y=40, s='%d' % c)
    #         c += 1
    #         last = t[i]
    # # plt.text(x=last + (t[i] - last) / 2 - 0.1, y=40, s='%d' % c)
    #
    # # -------------------- Figure 2: Load dev -----------------------
    #
    # plt.figure(4)
    # plt.subplot(211)
    # plt.grid(axis='y')
    # plt.plot(t, y3, 'g-', linewidth=2)
    # plt.title('Cumulative cost due to unserved load')
    # plt.ylabel('cumulative cost')
    # plt.xlim([0, t[-1]])
    # plt.ylim(bottom=0)
    # # plt.legend(loc=2)
    #
    # c = 1
    # last = 0
    # for i in range(1, len(t)):
    #     if t[i] == t[i-1]:
    #         plt.axvline(x=t[i], c='black')
    #         plt.text(x=last + (t[i] - last)/2 - 0.1, y=15000, s='%d' % c)
    #         c += 1
    #         last = t[i]
    # plt.text(x=last + (t[i] - last) / 2 - 0.1, y=15000, s='%d' % c)
    #
    #
    # labels = np.concatenate((ideal_state['fixed load'][:, 0], ideal_state['dispatch load'][:, 0]))
    # labels = labels[sum(load_dev_el) > 0.01]
    # labels = ['bus %d' % l for l in labels]
    # load_dev_el = load_dev_el[:, sum(load_dev_el) > 0.01]
    # load_dev_el = load_dev_el[:, np.argsort(load_dev_el[0])]
    # plt.subplot(212)
    # plt.grid(axis='y')
    # plt.stackplot(t, load_dev_el.T, baseline='zero', labels=labels)
    # plt.title('Unserved load by bus')
    # plt.xlabel('time (min)')
    # plt.ylabel('Power (MW)')
    # plt.xlim([0, t[-1]])
    # plt.legend(loc=1)
    # plt.tight_layout()
    #
    # c = 1
    # last = 0
    # for i in range(1, len(t)):
    #     if t[i] == t[i-1]:
    #         plt.axvline(x=t[i], c='black')
    #         # plt.text(x=last + (t[i] - last)/2 - 0.1, y=30, s='%d' % c)
    #         c += 1
    #         last = t[i]
    # # plt.text(x=last + (t[i] - last) / 2 - 0.1, y=30, s='%d' % c)
    #
    # # -------------------- Figure 3: Loss dev -----------------------
    #
    # plt.figure(5)
    # plt.subplot(211)
    # plt.grid(axis='y')
    # # plt.plot(t, y1, 'b-', linewidth=2, label='Generator dispatch deviation')
    # plt.plot(t, y2, 'r-', linewidth=2)
    # plt.title('Cumulative cost due to loss deviation')
    # plt.ylabel('cumulative cost')
    # plt.xlim([0, t[-1]])
    # # plt.legend(loc=2)
    #
    # c = 1
    # last = 0
    # for i in range(1, len(t)):
    #     if t[i] == t[i - 1]:
    #         plt.axvline(x=t[i], c='black')
    #         plt.text(x=last + (t[i] - last) / 2 - 0.1, y=5, s='%d' % c)
    #         c += 1
    #         last = t[i]
    # # plt.text(x=last + (t[i] - last) / 2 - 0.1, y=5, s='%d' % c)
    #
    # # plt.figure(fig_num+1)
    # plt.subplot(212)
    # plt.grid(axis='y')
    # # plt.plot(t, gen_dev, 'b-', linewidth=2, label='Generator dispatch deviation')
    # plt.plot(t, loss_dev_el, 'r-', linewidth=2)
    # # plt.plot(t, load_dev, 'g-', linewidth=2, label='Load not served')
    # plt.title('System loss deviation')
    # plt.xlabel('time (min)')
    # plt.ylabel('Power (MW)')
    # plt.xlim([0, t[-1]])
    # plt.tight_layout()
    # # plt.legend(loc=0)
    #
    # c = 1
    # last = 0
    # for i in range(1, len(t)):
    #     if t[i] == t[i - 1]:
    #         plt.axvline(x=t[i], c='black')
    #         # plt.text(x=last + (t[i] - last) / 2 - 0.1, y=0, s='%d' % c)
    #         c += 1
    #         last = t[i]
    # # plt.text(x=last + (t[i] - last) / 2 - 0.1, y=0, s='%d' % c)


