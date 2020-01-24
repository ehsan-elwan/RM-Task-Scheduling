import configparser
from copy import deepcopy
from Plotter import *


def load_params(input_file):
    """
    # Parse the input.ini file into dictionary
    :rtype: Dictionary
    """
    config = configparser.ConfigParser()
    config.read(input_file)
    section = 'INPUT_FILES'
    param_dict = dict()
    for option in config.options(section):
        param_dict[option] = config.get(section, option)
    return param_dict


class Task:
    def __init__(self, tid, arrival_date, predecessor, successor, unit_of_work, deadline, period, power, repeat):
        self.tid = tid
        self.arrival_date = arrival_date
        self.predecessor = predecessor  # List of dependencies tasks []
        self.successor = successor
        self.unit_of_work = unit_of_work
        self.deadline = deadline
        self.period = period
        self.power = power
        self.repeat = repeat
        self.running = False
        self.server_id = None
        self.critical_time = 0


class Server:
    def __init__(self, server_id, static_power, performance, frequency, local_power_cap):
        self.server_id = server_id
        self.static_power = static_power
        self.performance = performance
        self.frequency = frequency  # List of frequency []
        self.local_power_cap = local_power_cap
        self.available_after = 0
        self.available = True
        self.current_task = None


class Parser:
    def __init__(self, params):
        predecessor = dict()
        successor = dict()
        tasks = []
        servers = []
        try:
            with open(params['job_file']) as f:
                next(f)
                for line in f:
                    try:
                        tmp = line.rstrip().split(" ")
                        tmp = list(map(int, tmp))
                        tid = tmp[0]
                        arrival_date = tmp[1]
                        uow = tmp[2]
                        deadline = tmp[3]
                        period = tmp[4]
                        power = tmp[5]
                        successor[tid] = []
                        predecessor[tid] = []
                        repeat = 0
                        if period > 0:
                            repeat = int(params['repeat']) - 1
                        tasks.append(
                            Task(tid, arrival_date, [], [], uow, deadline, period, power, repeat))
                    except ValueError:
                        pass
                    except Exception as exp:
                        print(exp)
        except FileNotFoundError:
            print("Couldn't find", params['job_file'], "file")
            print("try to check the file or try to use the full path in the input.ini")
            exit(1)

        try:
            with open(params['dependency_file']) as f:
                next(f)
                for line in f:
                    try:
                        tmp = line.rstrip().replace(' ', '').split("-")
                        tmp = list(map(int, tmp))
                        predecessor[tmp[1]].append(tmp[0])
                        successor[tmp[0]].append(tmp[1])

                    except ValueError:
                        pass
                    except Exception as exp:
                        print(exp)
        except FileNotFoundError:
            print("Couldn't find", params['dependency_file'], "file")
            print("try to check the file or try to use the full path in the input.ini")
            exit(1)

        # update tasks dependencies:
        for task in tasks:
            task.predecessor = predecessor.get(task.tid)
            task.successor = successor.get(task.tid)
            if not task.successor:
                task.critical_time = task.unit_of_work
        try:
            with open(params['server_file']) as f:
                next(f)
                for line in f:
                    try:
                        tmp = line.rstrip().split(" ")
                        sid = int(tmp[0])
                        static_power = int(tmp[1])
                        performance = int(tmp[2])
                        frequencies = (line[line.index('(') + 1:line.index(')')]).split(" ")
                        frequencies = list(map(float, frequencies))
                        local_power_cap = int(tmp[-1])
                        servers.append(Server(sid, static_power, performance, frequencies, local_power_cap))
                    except ValueError:
                        pass
                    except Exception as exp:
                        print(exp)
        except FileNotFoundError:
            print("Couldn't find", params['server_file'], "file")
            print("try to check the file or try to use the full path in the input.ini")
            exit(1)

        self.tasks = tasks
        self.servers = servers


class Scheduling:
    """
    # Super class Scheduling, contains the main functions for
    a scheduler functions that been used throughout different algorithms
    :argument tasks -> List of tasks to schedule
              Servers -> List of servers
              Power_cap -> global power capacity for the system
    """

    def __init__(self, tasks, servers, power_cap, frequency):
        self.tasks = tasks  # List of tasks
        self.task_dict = {t.tid: t for t in tasks}
        self.servers = servers
        self.power_cap = power_cap  # Global power capacity
        self.frequency = frequency - 1  # Selected frequency from 1 to 3
        self.current_time = 0
        self.energy = 0
        self.output = []
        self.__set_critical_time(tasks[0])

    def get_available_server(self, task):
        for server in self.servers:
            if server.available and (task.power + server.static_power) <= server.local_power_cap:
                return server

        print("cant find server for task:", task.tid)
        return None

    def __set_critical_time(self, task):
        if not task.successor:
            task.critical_time = task.unit_of_work
            return task.unit_of_work
        else:
            task.critical_time = task.unit_of_work + max(
                self.__set_critical_time(self.task_dict[t]) for t in task.successor)
            return task.critical_time

    def update_servers(self):
        for server in self.servers:
            if not server.available and server.available_after > 1:
                server.available_after -= server.performance
            else:
                server.available_after = 0
                server.available = True

                if server.current_task is not None:
                    server.current_task.running = False
                    tmp = server.current_task.successor
                    for task_id in tmp:
                        self.task_dict[task_id].predecessor.remove(server.current_task.tid)
                    server.current_task = None

    def __check_missed_deadline(self, task, server_perf):
        if (self.current_time + (task.unit_of_work / server_perf)) > task.deadline:
            print("!!! Task", task.tid, "has missed its deadline by",
                  (self.current_time + task.unit_of_work / server_perf) - (task.deadline + task.arrival_date), "!!!")

    def assign_task2server(self, server, task):
        self.output.append([task.tid, server.server_id, self.current_time,
                            self.current_time + task.unit_of_work / server.performance])
        print("Task", task.tid, "assigned to server", server.server_id, "start at:", self.current_time,
              "end at:",
              self.current_time + task.unit_of_work / server.performance)
        self.__check_missed_deadline(task, server.performance)
        task.running = True
        task.server_id = server.server_id
        server.available = False
        server.available_after = task.unit_of_work / server.performance
        server.current_task = task
        self.energy += server.static_power + (task.power / 20) * server.frequency[self.frequency] ** 3

    def write_results(self):
        tmp = "results.txt".split('.')
        file1 = open(tmp[0] + "_" + self.__class__.__name__ + "." + tmp[1], "w")  # write mode
        file1.write("#jobid server_id start end \n")
        for line in self.output:
            file1.write(" ".join(str(e) for e in line) + "\n")
        file1.close()


class WaveFront(Scheduling):
    """
    # Class WaveFront that extends the super class Scheduling
    # Implements the WaveFront algorithm
    # Write the output schedule to txt file "results_WaveFront.txt"
    # display the results using the provided plotter
    """

    def __get_ready_tasks(self, previous_ready_tasks):
        for t in self.tasks:
            if t not in previous_ready_tasks and not t.predecessor \
                    and t.arrival_date <= self.current_time and t.server_id is None:
                previous_ready_tasks.append(t)
        return previous_ready_tasks

    def __check_global_power(self):
        current_draw = 0
        for server in self.servers:
            current_draw += server.static_power
            if server.current_task is not None:
                current_draw += server.current_task.power
        return current_draw <= self.power_cap

    def __check_missed_deadline(self, task, server_perf):
        if (self.current_time + (task.unit_of_work / server_perf)) > task.deadline:
            print("!!! Task", task.tid, "has missed its deadline by",
                  (self.current_time + task.unit_of_work / server_perf) - (task.deadline + task.arrival_date), "!!!")

    def build_wavefront_table(self, max_time):
        print("#" * 60)
        print("WaveFront scheduling")
        treated_tasks = []
        ready_tasks = self.__get_ready_tasks([])
        while self.current_time < max_time:
            # print("##### ready tasks at time:", current_time, self.test(ready_tasks), "######")
            for task in ready_tasks:
                server = super().get_available_server(task)
                if server is not None:
                    super().assign_task2server(server, task)
                    treated_tasks.append(task)
                    if task.repeat > 0:
                        task_repeat = deepcopy(task)
                        task_repeat.repeat -= 1
                        task_repeat.arrival_date += task_repeat.period
                        task_repeat.deadline += task_repeat.period
                        task_repeat.server_id = None
                        self.tasks.append(task_repeat)
                        self.tasks.remove(task)
                        # print("task", task_repeat.tid, "will come back at", task_repeat.arrival_date)
                else:
                    print("No available servers for task:", task.tid, "at time:", self.current_time)
            if not self.__check_global_power():
                print(" !!! WARNING !!! : Power exceeded system capacity")
            self.current_time += 1
            super().update_servers()
            # update ready_tasks list:
            for t in treated_tasks:
                ready_tasks.remove(t)
            treated_tasks = []
            ready_tasks = self.__get_ready_tasks(ready_tasks)
        print("Total energy:", self.energy, "Watt")
        self.write_results()
        plot(input_data=self.output, label="WaveFront scheduling on multiple servers")

    def get_available_tasks_fifo(self, current_time):
        tmp = []
        for task in self.tasks:
            if task.arrival_date <= current_time:
                tmp.append(task)
        return tmp


class FIFO(Scheduling):
    """
    # Class FIFO that extends the super class Scheduling
    # Implements the FIFO algorithm
    # Write the output schedule to txt file "results_FIFO.txt"
    # display the results using the provided plotter
    """

    def __sort_fifo(self):
        self.tasks.sort(key=lambda t: t.arrival_date, reverse=False)

    def __get_ready_tasks(self):
        tmp = []
        print("Getting ready tasks for time:", self.current_time)
        for task in self.tasks:
            if task.server_id is None and task.arrival_date <= self.current_time and not task.predecessor:
                tmp.append(task)
        return tmp

    def __insert_in_sorted_fifo(self, t):
        insert_position = len(self.tasks) - 1
        count = 0
        while self.tasks[insert_position].arrival_date > t.arrival_date:
            insert_position -= 1
            count += 1
        if count > 0:
            self.tasks.insert(insert_position + 1, t)
        else:
            self.tasks.append(t)

    def build_fifo_table(self):
        print("#" * 60)
        print("FIFO scheduling")
        self.__sort_fifo()

        while self.tasks:

            while self.tasks[0].arrival_date > self.current_time:
                self.current_time += 1
                super().update_servers()

            task = self.tasks.pop(0)
            if not task.predecessor:
                # print("Time:", self.current_time, "Current task:", task.tid)
                server = super().get_available_server(task)
                if server is not None:
                    super().assign_task2server(server, task)
                    if task.repeat > 0:
                        task_repeat = deepcopy(task)
                        task_repeat.repeat -= 1
                        task_repeat.arrival_date = self.current_time + task_repeat.period
                        task_repeat.deadline += task_repeat.arrival_date
                        task_repeat.server_id = None
                        self.__insert_in_sorted_fifo(task_repeat)
                else:
                    self.tasks.insert(0, task)
                    self.current_time += 1
                    super().update_servers()
            else:
                self.tasks.insert(0, task)
                self.current_time += 1
                super().update_servers()
        print("Total energy:", self.energy, "Watt")
        self.write_results()
        plot(input_data=self.output, label="FIFO scheduling on multiple servers")


class CPM(Scheduling):
    """
    # Class CPM "Critical Path Merge" that extends the super class Scheduling
    # Implements the CPM algorithm
    # Write the output schedule to txt file "results_CPM.txt"
    # display the results using the provided plotter
    """

    def __get_critical_paths(self):
        tmp = deepcopy(self.tasks)
        paths = []
        while tmp:
            mx = 0
            mx_id = None
            for task in tmp:
                if task.critical_time > mx:
                    mx = task.critical_time
                    mx_id = task.tid
            cp = [mx_id]
            while self.task_dict[mx_id].successor:
                tmp_mx_id = 0
                mx = 0
                for suc_id in self.task_dict[mx_id].successor:
                    if mx < self.task_dict[suc_id].critical_time:
                        mx = self.task_dict[suc_id].critical_time
                        tmp_mx_id = suc_id
                cp.append(tmp_mx_id)
                mx_id = tmp_mx_id
            paths.append(cp)
            for tid in cp:
                for task in tmp:
                    if task.tid == tid:
                        tmp.remove(task)
                        break

        return paths

    def __find_available_server(self):
        mini = self.servers[0].available_after
        srv = self.servers[0]
        for i in range(1, len(self.servers)):
            if mini > self.servers[i].available_after:
                mini = self.servers[i].available_after
                srv = self.servers[i]
        return srv

    def build_cpm_table(self):
        print("#" * 60)
        print("CPM scheduling")
        critical_paths = self.__get_critical_paths()
        print("Critical paths:", critical_paths)
        for i in range(len(critical_paths)):
            server = self.__find_available_server()
            time = max(server.available_after, self.task_dict[critical_paths[i][0]].arrival_date)
            for tid in critical_paths[i]:
                task = self.task_dict[tid]
                self.output.append([task.tid, server.server_id, time,
                                    time + task.unit_of_work / server.performance])
                print("Task", task.tid, "assigned to server", server.server_id, "start at:", time,
                      "end at:",
                      time + task.unit_of_work / server.performance)
                time += (task.unit_of_work / server.performance)
                self.energy += server.static_power + (task.power / 20) * server.frequency[self.frequency] ** 3
                for successor in task.successor:
                    t = self.task_dict[successor]
                    t.arrival_date = max(t.arrival_date, time)
                server.available_after = time
                server.available = False
        print("Total energy:", self.energy, "Watt")
        self.write_results()
        plot(input_data=self.output,
             label="CPM scheduling on multiple servers \n Critical paths: " + str(critical_paths))


if __name__ == "__main__":
    print("test")
