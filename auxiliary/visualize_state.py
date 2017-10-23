from matplotlib import pyplot as plt
from matplotlib import animation
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np
from oct2py import octave


def visualize_state(ideal_case, ideal_state, state_list, fig_num=1, frames=20, save=False):
    color_map = {0: 'black',
                 1: 'green'}
    color_map_2 = {0: 'green',
                   1: 'red'}

    # Initialize figure
    fig = plt.figure(fig_num, figsize=(12, 12))
    plt.ion()
    ax1 = plt.subplot2grid((3, 2), (0, 0))
    ax2 = plt.subplot2grid((3, 2), (0, 1))
    ax3 = plt.subplot2grid((3, 2), (1, 0), colspan=2)
    ax4 = plt.subplot2grid((3, 2), (2, 0), colspan=2)

    # Generator state plot
    gen_max = ideal_case['gen'][(octave.isload(ideal_case['gen']) == 0).reshape((-1)), 8].reshape((-1,))
    gen_ideal = ideal_state['real gen'][:, 1].reshape((-1,))
    gen_bus = ideal_state['real gen'][:, 0].reshape((-1,))
    cap_order = np.argsort(gen_max, axis=0, kind='quicksort')
    gen_width = 0.25
    gen_x = np.arange(len(gen_max))
    ax1.set_xticks(gen_x)
    ax1.set_xticklabels(['bus %d' % i for i in gen_bus[cap_order]])
    ax1.set_title('Generator schedule')
    ax1.set_ylabel('Power (MW)')

    # Load state plot
    d_load_ideal = -ideal_state['dispatch load'][:, 1].reshape((-1,))
    d_load_bus = ideal_state['dispatch load'][:, 0].reshape((-1,))
    d_load_order = np.argsort(d_load_ideal, axis=0, kind='quicksort')

    f_load_ideal = ideal_state['fixed load'][:, 1].reshape((-1,))
    f_load_bus = ideal_state['fixed load'][:, 0].reshape((-1,))
    f_load_order = np.argsort(f_load_ideal, axis=0, kind='quicksort')

    load_width = 0.5
    load_x1 = np.arange(len(d_load_ideal))
    load_x2 = np.arange(len(load_x1) + 1, len(load_x1) + 1 + len(f_load_ideal))
    ticks = np.concatenate(
        (['b %d' % i for i in d_load_bus[d_load_order]], ['b %d' % i for i in f_load_bus[f_load_order]]))
    ax2.set_xticklabels(ticks)
    ax2.set_xticks(np.concatenate((load_x1, load_x2)))
    ax2.set_title('Load Profile')
    ax2.set_ylabel('Power (MW)')

    # Line state plot
    mva_rating = ideal_case['branch'][:, 5].reshape((-1,))
    real_inj_ideal = np.abs(ideal_state['real inj'][:, 2].reshape((-1,)))
    real_inj_buses = np.abs(ideal_state['real inj'][:, 0:2].reshape((-1, 2)))
    line_order = np.argsort(mva_rating, axis=0, kind='quicksort')
    line_width = 0.25
    line_x = np.arange(len(mva_rating))
    ax3.set_xticks(line_x)
    ticks = ['%d - %d' % (i[0], i[1]) for i in real_inj_buses[line_order]]
    ax3.set_xticklabels(ticks)
    ax3.set_title('Line loadings')
    ax3.set_ylabel('Power (MW)')
    # ax3.set_xlim([-1, len(line_order)])

    # Line SPA plot
    ax4.set_xticks(line_x)
    ticks = ['%d - %d' % (i[0], i[1]) for i in real_inj_buses[line_order]]
    ax4.set_xticklabels(ticks)
    ax4.set_title('Line SPA differences')
    ax4.set_ylabel('Degrees')
    # ax4.set_xlim([-1, len(line_order)])
    ax4.set_ylim([0, 40])

    # Init dynamic plot objects
    # line_spa_ref = ax4.plot(line_x, np.ones(len(line_x))*10, color='red', markersize=5)
    line_spa_ref = ax4.axhline(y=10, color='black', linewidth=2)
    gen_ideal = ax1.bar(gen_x - gen_width / 2, gen_ideal[cap_order], gen_width, align='center', alpha=0.9, color='blue')
    gen_cap = ax1.bar(gen_x, gen_max[cap_order], gen_width*2, align='center', alpha=0.3)
    gen_curr = ax1.bar(gen_x+gen_width/2, np.zeros(len(gen_x)), gen_width, align='center', alpha=0.9, color='red')
    d_ideal = ax2.bar(load_x1, d_load_ideal[d_load_order], load_width, align='center', alpha=0.2)
    d_curr = ax2.bar(load_x1, np.zeros(len(load_x1)), load_width, align='center', alpha=0.9, color='green')
    f_ideal = ax2.bar(load_x2, f_load_ideal[f_load_order], load_width, align='center', alpha=0.2)
    f_curr = ax2.bar(load_x2, np.zeros(len(load_x2)), load_width, align='center', alpha=0.9, color='green')
    line_ideal = ax3.bar(line_x - line_width / 2, real_inj_ideal[line_order], line_width, align='center', alpha=0.9, color='blue')
    line_rating = ax3.bar(line_x, mva_rating[line_order], line_width*2, align='center', alpha=0.3)
    line_curr = ax3.bar(line_x+line_width/2, np.zeros(len(line_x)), line_width, align='center', alpha=0.9, color='red')
    line_spa = ax4.bar(line_x, np.zeros(len(line_x)), line_width*2, align='center', alpha=0.9, color='green')

    gen_limit_patch = mpatches.Patch(color='green', alpha=0.2, label='Limit')
    gen_offline_patch = mpatches.Patch(color='black', alpha=0.2, label='Offline')
    gen_ideal_patch = mpatches.Patch(color='blue', alpha=0.9, label='Ideal state')
    gen_current_patch = mpatches.Patch(color='red', alpha=0.9, label='Current state')

    load_ideal_patch = mpatches.Patch(color='blue', alpha=0.2, label='Ideal state')
    load_offline_patch = mpatches.Patch(color='black', alpha=0.2, label='Blackout')
    load_current_patch = mpatches.Patch(color='green', alpha=0.9, label='Current state')

    line_limit_patch = mpatches.Patch(color='green', alpha=0.2, label='Limit')
    line_offline_patch = mpatches.Patch(color='black', alpha=0.2, label='Offline')
    line_ideal_patch = mpatches.Patch(color='blue', alpha=0.9, label='Ideal state')
    line_current_patch = mpatches.Patch(color='red', alpha=0.9, label='Current state')

    spa_green = mpatches.Patch(color='green', alpha=0.9, label='Line SPA diff')
    spa_red = mpatches.Patch(color='red', alpha=0.9, label='Line in question')
    spa_limit = mlines.Line2D([], [], color='black', label='SPA diff limit')

    ax1.legend(handles=[gen_limit_patch, gen_offline_patch, gen_ideal_patch, gen_current_patch], loc='upper left')
    ax2.legend(handles=[load_ideal_patch, load_offline_patch, load_current_patch], loc='upper right')
    ax3.legend(handles=[line_limit_patch, line_offline_patch, line_ideal_patch, line_current_patch], loc='upper left')
    ax4.legend(handles=[spa_green, spa_red, spa_limit], loc='upper left')

    def update(frame):
        # Manipulate frame
        list_ind = int(np.floor(frame/frames))
        between_frame = frame % frames

        # Generator color
        gen_island = state_list[list_ind]['real gen'][cap_order, -1]
        for rect, color in zip(gen_cap, [color_map[ind] for ind in gen_island]):
            rect.set_color(color)

        # Generator values
        gen_current_1 = state_list[list_ind]['real gen'][cap_order, 1].reshape((-1,))
        gen_current_2 = state_list[list_ind+1]['real gen'][cap_order, 1].reshape((-1,))
        gen_current_3 = gen_current_1 + (gen_current_2-gen_current_1)*(between_frame/frames)
        for rect, height in zip(gen_curr, gen_current_3):
            rect.set_height(height)

        # Load color
        d_load_island = state_list[list_ind]['dispatch load'][d_load_order, -1]
        f_load_island = state_list[list_ind]['fixed load'][f_load_order, -1]
        for rect, color in zip(d_ideal, [color_map[ind] for ind in d_load_island]):
            rect.set_color(color)
        for rect, color in zip(f_ideal, [color_map[ind] for ind in f_load_island]):
            rect.set_color(color)

        # Load values
        d_load_current_1 = -state_list[list_ind]['dispatch load'][d_load_order, 1].reshape((-1,))
        d_load_current_2 = -state_list[list_ind+1]['dispatch load'][d_load_order, 1].reshape((-1,))
        d_load_current_3 = d_load_current_1 + (d_load_current_2-d_load_current_1)*(between_frame/frames)
        f_load_current = state_list[list_ind]['fixed load'][f_load_order, 1].reshape((-1,))
        for rect, height in zip(d_curr, d_load_current_3):
            rect.set_height(height)
        for rect, height in zip(f_curr, f_load_current):
            rect.set_height(height)

        # Line color
        line_island = state_list[list_ind]['real inj'][line_order, -1]
        for rect, height in zip(line_rating, [color_map[ind] for ind in line_island]):
            rect.set_color(height)

        # Line values
        real_inj_current_1 = np.abs(state_list[list_ind]['real inj'][line_order, 2].reshape((-1,)))
        real_inj_current_2 = np.abs(state_list[list_ind+1]['real inj'][line_order, 2].reshape((-1,)))
        real_inj_current_3 = real_inj_current_1 + (real_inj_current_2-real_inj_current_1)*(between_frame/frames)
        for rect, height in zip(line_curr, real_inj_current_3):
            rect.set_height(height)

        # Line SPA diff (Don't hate me for this ridiculous list comprehension)
        SPA_bus1_1 = [state_list[list_ind]['bus voltage angle'][state_list[list_ind]['bus voltage angle'][:, 0] == i, 1] for i in state_list[list_ind]['real inj'][line_order, 0]]
        SPA_bus2_1 = [state_list[list_ind]['bus voltage angle'][state_list[list_ind]['bus voltage angle'][:, 0] == i, 1] for i in state_list[list_ind]['real inj'][line_order, 1]]
        SPA_diff_1 = np.abs(np.array(SPA_bus1_1) - np.array(SPA_bus2_1))
        SPA_bus1_2 = [state_list[list_ind+1]['bus voltage angle'][state_list[list_ind+1]['bus voltage angle'][:, 0] == i, 1] for i in state_list[list_ind+1]['real inj'][line_order, 0]]
        SPA_bus2_2 = [state_list[list_ind+1]['bus voltage angle'][state_list[list_ind+1]['bus voltage angle'][:, 0] == i, 1] for i in state_list[list_ind+1]['real inj'][line_order, 1]]
        SPA_diff_2 = np.abs(np.array(SPA_bus1_2) - np.array(SPA_bus2_2))
        SPA_diff_3 = SPA_diff_1 + (SPA_diff_2-SPA_diff_1)*(between_frame/frames)
        for rect, height in zip(line_spa, SPA_diff_3):
            rect.set_height(height)

        # Detect if line state changes, if so, make it red
        line_state_change = (state_list[list_ind+1]['real inj'][line_order, -1] - state_list[list_ind]['real inj'][line_order, -1])
        for rect, color in zip(line_spa, [color_map_2[i] for i in line_state_change]):
            rect.set_color(color)
        list_ind
        if state_list[list_ind+1]['Title']:
            plt.suptitle(state_list[list_ind+1]['Title'], fontsize=18)
        else:
            plt.suptitle('')

        return gen_cap, gen_curr, d_ideal, f_ideal, d_curr, f_curr, line_ideal, line_rating, line_curr, line_spa

    animate = animation.FuncAnimation(fig, update, frames=(len(state_list)-1)*frames-1, interval=20)
    plt.show()

    if save:
        animate.save('Animate.gif', writer='imagemagick', dpi=40)

    return animate
