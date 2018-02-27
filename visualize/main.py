from visualize.visualize_cost_opt_ga import visualize_cost_opt_ga
from glob import glob
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


plt.rc('text', usetex=True)
plt.rc('font', family='serif')
sns.set_palette("Set1")
cp = sns.color_palette()

# Directory info
directory = '/home/alexander/Documents/Thesis Work/PowerSystem-RL/data/'
ga_folders = ['ga-eta25-d6', 'ga-eta50-d6', 'ga-eta75-d6']
ts_folders = ['ts-uniform-d6', 'ts-cost-d6', 'ts-rank-d6']#, 'ts-inverse_rank-d6', 'ts-inverse_cost-d6']

ga_low = []
ga_seq = []
ts_low = []

# Extract ga files
for folder in ga_folders:
    files = glob(directory + folder + '/*')

    low = []
    seq = []
    # Each file represents one optimization
    for file in files:
        with open(file, 'rb') as f:
            data = pickle.load(f)
            low.append(data['best_total_cost_store'])
            seq.append(data['action_sequence_store'])

    ga_low.append(low)
    ga_seq.append(seq)

# Extract ts files
for folder in ts_folders:
    files = glob(directory + folder + '/*')

    low = []
    # Each file represents one optimization
    for file in files:
        with open(file, 'rb') as f:
            data = pickle.load(f)
            low.append(data['best_total_cost_store'])

    ts_low.append(low)


# Calculate the ga lower envelope mean upper and lower envelopes
ga = np.array(ga_low)
ga_mean_min_envelopes = []
plt.figure(1)
for i in range(len(ga_folders)):

    mean_min = np.mean(ga[i, :, :], axis=0)
    # Scale the x axis to actions
    x_ticks = np.linspace(0, 2100, len(mean_min))
    ga_mean_min_envelopes.append(mean_min)
    # plot
    plt.plot(x_ticks, mean_min, linewidth='2', linestyle='-', label=ga_folders[i])

# Truncate optimizations to the shortest one
ts = []
for i, opti in enumerate(ts_low):
    min_len = np.min([len(row) for row in opti])
    ts.append(np.array([row[0:min_len] for row in opti]))

# Plot ts optimizations
ts_mean_min_envelopes = []
for i in range(len(ts_folders)):

    mean_min = np.mean(ts[i], axis=0)
    # Scale the x axis to actions
    x_ticks = np.linspace(0, 2100, len(mean_min))
    ts_mean_min_envelopes.append(mean_min)
    plt.plot(x_ticks, mean_min, linewidth='2', linestyle='--', label=ts_folders[i])

plt.title('Optimization methods')
plt.legend(['GA $\eta=0.25$', 'GA $\eta=0.50$','GA $\eta=0.75$','TS uniform ','TS cost','TS rank'])
# plt.legend()
plt.xlabel('Actions executed')
plt.ylabel('Restoration cost')
plt.xlim([0, 2100])



# ----- testing --------

with open('/home/alexander/Documents/Thesis Work/PowerSystem-RL/data/ga-eta65-d6-test/optimization_11.pickle', 'rb') as f:
    data = pickle.load(f)

data['best_total_cost_store']

for i in data['action_sequence_store'][-1]:

    print('%s & %s \\\\' % (data['action map'][i][0], data['action map'][i][1]))

# --------------- Visualize state ---------------

from oct2py import octave
from auxiliary.config_case30 import mp_opt, deconstruct_6,\
    dispatchable_loads, ramp_rates, dispatch_load_cost, fixed_load_cost, loss_cost, disp_dev_cost
from system.PowerSystem import PowerSystem
from system.execute_sequence import execute_sequence_2
from objective.objective_function import objective_function
from visualize.visualize_state import visualize_state
from visualize.visualize_cost import visualize_cost
import pickle
import numpy as np
from objective.power_deviation import power_deviation


metadata = {'mp_opt': mp_opt,
            'ramp_rates': ramp_rates,
            'dispatch_load_cost': dispatch_load_cost,
            'fixed_load_cost': fixed_load_cost,
            'loss_cost': loss_cost,
            'disp_dev_cost': disp_dev_cost,
            'gen_load_char': None,
            'dispatchable_loads': dispatchable_loads}

# Instantiate PowerSystem object
np.set_printoptions(precision=2)
base_case = octave.loadcase('case30')
# base_case['branch'][:, 5] = line_ratings  # Only necessary for case 14
base_result = octave.runpf(base_case, mp_opt)
ps = PowerSystem(base_result,
                 metadata,
                 spad_lim=10,
                 deactivated=deconstruct_6,
                 verbose=1,
                 verbose_state=0)

with open('/home/alexander/Documents/Thesis Work/PowerSystem-RL/data/iceland_test/optimization_10.pickle', 'rb') as f:
    data = pickle.load(f)
sequence = data['action_sequence_store'][-1]
action_map = data['action map']

state_list, island_list = execute_sequence_2(ps, sequence, action_map)
time_store, energy_store, cost_store = objective_function(state_list, ps.ideal_state, metadata)
[gen_dev, load_dev, loss_dev] = power_deviation(state_list, ps.ideal_state)

# visualize_state(ps.ideal_case, ps.ideal_state, state_list, fig_num=1, frames=10, save=False)
visualize_cost(time_store, cost_store, energy_store, gen_dev, load_dev, loss_dev)





