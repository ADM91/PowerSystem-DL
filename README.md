# PowerSystem-RL #
This project explores reinforcement learning (RL) methods on small
scale power systems after faults.  The primary objective is for the RL agent to prevent system failure, and a second
objective is to minimize steady state rotor angle variation to set the system up for reconnection
of the lost power line.  The envisioned progression of the project is to start with simple power system simulation
and RL models and gradually increase their complexities until computing limits or time constraints are
reached.  An optimistic (in terms of time) list of RL algorithms that will be investigated is listed below.

The simplest IEEE power system models will be used as proof of concept because they are easy to visualize and think about.
A steady state power flow simulation using **PyPower** (direct port of MATPOWER)
will be used, then hopefully the project will graduate to a dynamic temporal simulation model: **PyPower-Dynamic**.
Visualization of the data and power system network will be emphasized because it facilitates
understanding of the problem and results.  The package **NetworkX** is used for graph visualization.

## Current dependencies ##
* pypower
* networkx
* matplotlib
* numpy

## Objective function brainstorm ##
Rotor angles (generators) / Voltage angles (buses)
* Minimize the total variance
* Minimize maximum difference in angle
* Minimize the difference on either side of fault
Line loadings
* Minimize the maximum (minimax) the percentage of rated load flow on each line

## Control parameter brainstorm ##
* Generator power setpoints... (maybe not, this is solved in power flow sim)
* Generator droop/ramp rates (this should only apply to varying loads, but exists as a parameter in MATPOWER and PyPower)

## Initial assumptions (these will be reduced in future implementations) ##
* No possibility of cascading faults
* Steady state solution is sufficient and accurate (with intention to move to a dynamic model)
* Automated processes are ignored (breaker line tripping, demand side management, etc.)

## Methods of RL that will (optimistically) be investigated ##
Need to find and read and cite papers on each method...
* Cross-entropy method (CEM)
* Policy Gradient (PG)
* Deep Q-Networks (DQN)
* Actor Critic Agents (AC, A3C)
