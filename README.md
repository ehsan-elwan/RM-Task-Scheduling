# RM-Task-Scheduling
Simulation of Task Scheduling

RM-Task-Scheduling is a Python3 script, The main goal is to simulate and compare different algorithms (WaveFront, FIFO, Critical path merge) for the resource management of a system.

## Installation

Download and Unzip RM-Task-Scheduling.zip file, to run the software use:

## Run Example
```bash
python3 ./main.py
```

## Usage

```text
input.ini is the input file which contains the input files and resources for the simulator With the following format:
```

```ini
[INPUT_FILES]

job_file = jobs.txt
server_file = servers.txt
dependency_file = dependencies.txt
power_cap = 1000
energy_cap = 100000
repeat = 2
frequency = 1
max_timesteps = 150
```

## job_file example:

```text
# idjob arrival date, units of work, deadline, period, power
0 0 10 15 0 50
1 0 5 10 20 10
2 3 6 10 10 20
3 4 10 30 0 50
4 5 10 30 0 50
5 6 4 12 0 10
```

## server_file example:

```text
#idserver static_power, performance (#number of unit of work per time step at minimum frequency), frequencies, local_power_cap
0 20 1 (1 1.5 2 3) 100 
1 50 1 (1 1.5 2 3) 100 
2 50 1 (1 2 3) 150 
3 40 2 (1 3) 200
```

## dependency_file example:
```text
# task0 - task1 : task1 depends on task0 
0 - 3
0 - 4
3 - 5
3 - 9 
5 - 8
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
