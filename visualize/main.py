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

