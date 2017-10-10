import time
from matplotlib import pyplot as plt
from matplotlib import animation
import numpy as np
from oct2py import octave


def visualize_state(ideal_case, ideal_state, state_list, fig_num=1):
    color_map = {0: 'black',
                 1: 'green'}

    # Initialize figure
    fig = plt.figure(1, figsize=(12, 12))
    plt.ion()
    ax1 = plt.subplot2grid((2, 2), (0, 0))
    ax2 = plt.subplot2grid((2, 2), (0, 1))
    ax3 = plt.subplot2grid((2, 2), (1, 0), colspan=2)

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
    plt.xlim([-1, len(line_order)])

    # plt.tight_layout()

    # Init dynamic plot objects
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

    ax3.legend(['Line limit', 'Ideal load', 'Current load'], loc='upper left')
    ax2.legend(['Ideal load', 'Current load'], loc='upper left')
    ax1.legend(['Generator limit', 'Ideal state', 'Current state'], loc='upper left')

    # dyn_objects = [gen_cap, gen_curr, d_ideal, d_curr, f_ideal, f_curr, line_rating, line_curr]

    def init():
        for i, b in enumerate(gen_curr):
            b.set_height(0)
        return gen_curr

    def update(frame):
        # Manipulate frame
        list_ind = int(np.floor(frame/20))
        between_frame = frame % 20

        # Generator color
        gen_island = state_list[list_ind]['real gen'][cap_order, -1]
        for rect, color in zip(gen_cap, [color_map[ind] for ind in gen_island]):
            rect.set_color(color)

        # Generator values
        gen_current_1 = state_list[list_ind]['real gen'][cap_order, 1].reshape((-1,))
        gen_current_2 = state_list[list_ind+1]['real gen'][cap_order, 1].reshape((-1,))
        gen_current_3 = gen_current_1 + (gen_current_2-gen_current_1)*(between_frame/20)
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
        d_load_current_3 = d_load_current_1 + (d_load_current_2-d_load_current_1)*(between_frame/20)
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
        real_inj_current_3 = real_inj_current_1 + (real_inj_current_2-real_inj_current_1)*(between_frame/20)
        for rect, height in zip(line_curr, real_inj_current_3):
            rect.set_height(height)

        return gen_cap, gen_curr, d_ideal, f_ideal, d_curr, f_curr, line_ideal, line_rating, line_curr

    for i in range(len(state_list)):
        print(state_list[i]['real gen'][cap_order, 1])

    print(len(state_list))

    anim = animation.FuncAnimation(fig, update, frames=(len(state_list)-1)*20-1, interval=20)
    plt.show()

    return anim

    # def update(frame):
    #
    #     print(frame)
    #
    #     # Clear the last set of data
    #     # for obj in dyn_objects:
    #     #     obj.clear()
    #
    #     gen_current = state_list[frame]['real gen'][:, 1].reshape((-1,)) + 100
    #     gen_island = state_list[frame]['real gen'][cap_order, -1]
    #     dyn_objects[0].set_data(gen_x, gen_max[cap_order])
    #     # dyn_objects[0].set_color([color_map[ind] for ind in gen_island])
    #     dyn_objects[1].set_data(gen_x + gen_width / 2, gen_current[cap_order])

        # dyn_objects[1], = ax1.bar(gen_x + gen_width / 2, gen_current[cap_order], gen_width, align='center', alpha=0.9,
        #                           color='red')
        #
        # # Load state plot dynamic data
        # d_load_current = -state_list[frame]['dispatch load'][:, 1].reshape((-1,))
        # d_load_island = state_list[frame]['dispatch load'][d_load_order, -1]
        # f_load_current = state_list[frame]['fixed load'][:, 1].reshape((-1,))
        # f_load_island = state_list[frame]['fixed load'][f_load_order, -1]
        # dyn_objects[2], = ax2.bar(load_x1, d_load_ideal[d_load_order], load_width, align='center', alpha=0.2,
        #                           color=[color_map[ind] for ind in d_load_island])
        # dyn_objects[3], = ax2.bar(load_x1, d_load_current[d_load_order], load_width, align='center', alpha=0.9,
        #                           color=[color_map[ind] for ind in d_load_island])
        # dyn_objects[4], = ax2.bar(load_x2, f_load_ideal[f_load_order], load_width, align='center', alpha=0.2,
        #                           color=[color_map[ind] for ind in f_load_island])
        # dyn_objects[5], = ax2.bar(load_x2, f_load_current[f_load_order], load_width, align='center', alpha=0.9,
        #                           color=[color_map[ind] for ind in f_load_island])
        #
        # # Line state plot dynamic data
        # real_inj_current = np.abs(state_list[frame]['real inj'][:, 2].reshape((-1,)))
        # line_island = state_list[frame]['real inj'][line_order, -1]
        # dyn_objects[6], = ax3.bar(line_x, mva_rating[line_order], line_width * 2, align='center', alpha=0.3,
        #                           color=[color_map[ind] for ind in line_island])
        # dyn_objects[7], = ax3.bar(line_x + line_width / 2, real_inj_current[line_order], line_width, align='center',
        #                           alpha=0.9, color='red')

        # Generator state plot dynamic data
        # gen_current = state_list[frame]['real gen'][:, 1].reshape((-1,))
        # gen_island = state_list[frame]['real gen'][cap_order, -1]
        # dyn_objects[0], = ax1.bar(gen_x, gen_max[cap_order], gen_width * 2, align='center', alpha=0.3,
        #                           color=[color_map[ind] for ind in gen_island])
        # dyn_objects[1], = ax1.bar(gen_x + gen_width / 2, gen_current[cap_order], gen_width, align='center', alpha=0.9,
        #                           color='red')
        #
        # # Load state plot dynamic data
        # d_load_current = -state_list[frame]['dispatch load'][:, 1].reshape((-1,))
        # d_load_island = state_list[frame]['dispatch load'][d_load_order, -1]
        # f_load_current = state_list[frame]['fixed load'][:, 1].reshape((-1,))
        # f_load_island = state_list[frame]['fixed load'][f_load_order, -1]
        # dyn_objects[2], = ax2.bar(load_x1, d_load_ideal[d_load_order], load_width, align='center', alpha=0.2,
        #                           color=[color_map[ind] for ind in d_load_island])
        # dyn_objects[3], = ax2.bar(load_x1, d_load_current[d_load_order], load_width, align='center', alpha=0.9,
        #                           color=[color_map[ind] for ind in d_load_island])
        # dyn_objects[4], = ax2.bar(load_x2, f_load_ideal[f_load_order], load_width, align='center', alpha=0.2,
        #                           color=[color_map[ind] for ind in f_load_island])
        # dyn_objects[5], = ax2.bar(load_x2, f_load_current[f_load_order], load_width, align='center', alpha=0.9,
        #                           color=[color_map[ind] for ind in f_load_island])
        #
        # # Line state plot dynamic data
        # real_inj_current = np.abs(state_list[frame]['real inj'][:, 2].reshape((-1,)))
        # line_island = state_list[frame]['real inj'][line_order, -1]
        # dyn_objects[6], = ax3.bar(line_x, mva_rating[line_order], line_width * 2, align='center', alpha=0.3,
        #                           color=[color_map[ind] for ind in line_island])
        # dyn_objects[7], = ax3.bar(line_x + line_width / 2, real_inj_current[line_order], line_width, align='center',
        #                           alpha=0.9, color='red')

        # if state_list[frame]['Title']:
        #     plt.suptitle(state_list[frame]['Title'], labelsize=18)
        # else:
        #     plt.suptitle('')

        # return dyn_objects,

    # print('Here')
    #
    # anim = animation.FuncAnimation(fig, update, frames=len(state_list), interval=1000)
    # print('Here too')
    #
    # plt.show()
    #
    # print('Here three')
