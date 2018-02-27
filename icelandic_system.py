import numpy as np
from oct2py import octave
from auxiliary.config_iceland import mp_opt,\
    dispatchable_loads,\
    ramp_rates,\
    dispatch_load_cost,\
    fixed_load_cost,\
    loss_cost,\
    disp_dev_cost, \
    gen_load_char,\
    line_map
from system.PowerSystem import PowerSystem
from system.pick_random_state import pick_random_state
from system.combine_gen import combine_gen

metadata = {'mp_opt': mp_opt,
            'ramp_rates': ramp_rates,
            'dispatch_load_cost': dispatch_load_cost,
            'fixed_load_cost': fixed_load_cost,
            'loss_cost': loss_cost,
            'disp_dev_cost': disp_dev_cost,
            'gen_load_char': gen_load_char,
            'dispatchable_loads': dispatchable_loads}

# Instantiate PowerSystem object
np.set_printoptions(precision=2)
# base_case = octave.loadcase('/home/alexander/Documents/MATLAB/alex parser/MPCfiles/PSSE_Landsnet_09_06_2017__16_02_29.mat')
base_case = pick_random_state(octave)
base_case.gen, base_case.gencost = combine_gen(base_case.gen, base_case.gencost)
base_result = octave.runpf(base_case, mp_opt)
ps = PowerSystem(metadata, spad_lim=20, deactivated=1, verbose=1, verbose_state=0)
ps.set_ideal_case(base_result)

# ----------Test opf----------
# base_result_pf = octave.runpf(base_result)
# # manipulate gencost matrix
# base_result_pf['gencost'] = np.append(base_result_pf['gencost'], np.zeros((np.shape(base_result_pf['gencost'])[0], 3)), axis=1)
# # Add a constrained gen
# base_result_pf['gencost'][0:12] = ps.islands['0']['gencost'][0:12]
# # Run opf
# base_result_opf = octave.runopf(base_result_pf)

# Problem found: If generator is set to 0, the cost curve is flat and opf doesn't converge
# Solution: remove the generator form case -or- set cost curve to a positive slope


ps = pick_random_state()

# ----------------Inspection of Icelandic system -------------------------
count = 1
for a, b in zip(base_case.bus_name,base_case.bus_nameOLD):
    print(count,a,b)
    count += 1

# List the bus names that I have chosen
buses = [52,51,48,54,49,71,70,72,73,50,55,74,46,44,56]
for b in buses:
    print(base_case.bus_name[b-1])

# List the lines connecting my buses:
line_map = [line[0] in buses and line[1] in buses for line in base_case.branch]
















