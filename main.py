from scheduler import *

# Parse the input.ini file into python dictionary
parameters = load_params('input.ini')
# Parse tasks, servers and dependencies files to objects
data = Parser(parameters)
# Maximum time steps used only for WaveFront algorithm
max_time = int(parameters['max_timesteps'])
# Global power capacity available
power_cap = int(parameters['power_cap'])
# Selected frequency 1,2 or 3:
frq = int(parameters['frequency'])
# initializing scheduler for each algorithm
wave_front = WaveFront(tasks=deepcopy(data.tasks), servers=deepcopy(data.servers), power_cap=power_cap, frequency=frq)
fifo = FIFO(tasks=deepcopy(data.tasks), servers=deepcopy(data.servers), power_cap=power_cap, frequency=frq)
cpm = CPM(tasks=deepcopy(data.tasks), servers=deepcopy(data.servers), power_cap=power_cap, frequency=frq)
# Build scheduling tables
wave_front.build_wavefront_table(max_time=max_time)
fifo.build_fifo_table()
cpm.build_cpm_table()
