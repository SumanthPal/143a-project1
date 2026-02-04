### Fill in the following information before submitting
# Group id: 2
# Members: Isha Kotalwar, Arnav Pandey, Sumanth Pallamreddy

from collections import deque

# PID is just an integer, but it is used to make it clear when a integer is expected to be a valid PID.
PID = int

# This class represents the PCB of processes.
# It is only here for your convinience and can be modified however you see fit.
class PCB: 
    pid: PID

    def __init__(self, pid: PID):
        self.pid = pid
        self.priority = 0
        self.time_remaining = 0  # For RR scheduler

# This class represents the Kernel of the simulation.
# The simulator will create an instance of this object and use it to respond to syscalls and interrupts.
# DO NOT modify the name of this class or remove it.
class Kernel:
    scheduling_algorithm: str
    ready_queue: deque[PCB]
    waiting_queue: deque[PCB]
    running: PCB
    idle_pcb: PCB

    # Called before the simulation begins.
    # Use this method to initilize any variables you need throughout the simulation.
    # logger is provided which allows you to include your own print statements in the
    #   output logs. These will not impact grading.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def __init__(self, scheduling_algorithm: str, logger):
        self.scheduling_algorithm = scheduling_algorithm
        self.ready_queue = deque()
        self.waiting_queue = deque()
        self.idle_pcb = PCB(0)
        self.running = self.idle_pcb
        self.logger = logger
        
        self.time_quantum = 40 
        
        # For Multilevel scheduler
        self.foreground_queue = deque() 
        self.background_queue = deque() 
        self.current_level = "Foreground" 
        self.level_time = 0  
        self.level_switch_time = 200 

    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def new_process_arrived(self, new_process: PID, priority: int, process_type: str) -> PID:
        new_pcb = PCB(new_process)
        new_pcb.priority = priority
        
        if self.scheduling_algorithm == "Multilevel":
            if process_type == "Foreground":
                new_pcb.time_remaining = self.time_quantum
                self.foreground_queue.append(new_pcb)
            else: 
                self.background_queue.append(new_pcb)
            
            # If currently idle, need to start running and set up level properly
            if self.running.pid == 0:
                # Prioritize foreground over background when starting from idle
                if len(self.foreground_queue) > 0:
                    self.current_level = "Foreground"
                    self.level_time = 0
                elif len(self.background_queue) > 0:
                    self.current_level = "Background"
                    self.level_time = 0
                self.running = self.choose_next_process()
        elif self.scheduling_algorithm == "RR":
            new_pcb.time_remaining = self.time_quantum
            self.ready_queue.append(new_pcb)
            
            if self.running.pid == 0:
                self.running = self.choose_next_process()
        elif self.scheduling_algorithm == "Priority":
            self.ready_queue.append(new_pcb)
            self.ready_queue = deque(sorted(self.ready_queue, key=lambda pcb: (pcb.priority, pcb.pid)))
            
            if self.running.pid == 0 or self.running.priority > priority:
                if self.running.pid != 0:
                    self.ready_queue.append(self.running)
                    self.ready_queue = deque(sorted(self.ready_queue, key=lambda pcb: (pcb.priority, pcb.pid)))
                self.running = self.choose_next_process()
        else: 
            self.ready_queue.append(new_pcb)
            if self.running.pid == 0:
                self.running = self.choose_next_process()
        
        return self.running.pid

    # This method is triggered every time the current process performs an exit syscall.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_exit(self) -> PID:
        if self.scheduling_algorithm == "Multilevel":
            # Check current level first
            if self.current_level == "Foreground":
                if len(self.foreground_queue) > 0:
                    # Stay in foreground
                    self.running = self.choose_next_process()
                elif len(self.background_queue) > 0:
                    # Switch to background
                    self.current_level = "Background"
                    self.level_time = 0
                    self.running = self.choose_next_process()
                else:
                    # No processes
                    self.running = self.idle_pcb
            else:  # Background
                if len(self.background_queue) > 0:
                    # Stay in background
                    self.running = self.choose_next_process()
                elif len(self.foreground_queue) > 0:
                    # Switch to foreground
                    self.current_level = "Foreground"
                    self.level_time = 0
                    self.running = self.choose_next_process()
                else:
                    # No processes
                    self.running = self.idle_pcb
        else:
            self.running = self.choose_next_process()
        return self.running.pid
    

    # This is where you can select the next process to run.
    # This method is not directly called by the simulator and is purely for your convinience.
    # Feel free to modify this method as you see fit.
    # It is not required to actually use this method but it is recommended.
    def choose_next_process(self):
        if self.scheduling_algorithm == "FCFS":
            if len(self.ready_queue) == 0:
                return self.idle_pcb
            return self.ready_queue.popleft()
        
        elif self.scheduling_algorithm == "Priority":
            if len(self.ready_queue) == 0:
                return self.idle_pcb
            return self.ready_queue.popleft()
        
        elif self.scheduling_algorithm == "RR":
            if len(self.ready_queue) == 0:
                return self.idle_pcb
            next_pcb = self.ready_queue.popleft()
            next_pcb.time_remaining = self.time_quantum
            return next_pcb
        elif self.scheduling_algorithm == "Multilevel":
            if self.current_level == "Foreground":
                if len(self.foreground_queue) > 0:
                    next_pcb = self.foreground_queue.popleft()
                    next_pcb.time_remaining = self.time_quantum
                    return next_pcb
                return self.idle_pcb
            else: 
                if len(self.background_queue) > 0:
                    return self.background_queue.popleft()
                return self.idle_pcb 
        
        else:
            self.logger("Unknown scheduling algorithm")
            return self.idle_pcb

    # This method is triggered when the currently running process requests to change its priority.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_set_priority(self, new_priority: int) -> PID:
        self.running.priority = new_priority
        if self.scheduling_algorithm == "Priority":
            if self.running.pid != 0:
                self.ready_queue.append(self.running)
                self.ready_queue = deque(sorted(self.ready_queue, key=lambda pcb: (pcb.priority, pcb.pid)))
            self.running = self.choose_next_process()
        return self.running.pid

    # This function represents the hardware timer interrupt.
    # It is triggered every 10 milliseconds and is the only way a kernel can track passing time.
    # Do not use real time to track how much time has passed as time is simulated.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def timer_interrupt(self) -> PID:
        if self.scheduling_algorithm == "RR":
            if self.running.pid != 0:
                self.running.time_remaining -= 10
                
                if self.running.time_remaining <= 0:
                    self.ready_queue.append(self.running)
                    self.running = self.choose_next_process()
        
        elif self.scheduling_algorithm == "Multilevel":
            self.level_time += 10
            if self.running.pid != 0 and self.current_level == "Foreground":
                self.running.time_remaining -= 10
                if self.running.time_remaining <= 0:
                    self.foreground_queue.append(self.running)
                    self.running = self.choose_next_process()
                    return self.running.pid
            
            if self.level_time >= self.level_switch_time:
                if self.current_level == "Foreground":
                    if len(self.background_queue) > 0:
                        if self.running.pid != 0:
                            self.foreground_queue.append(self.running)
                        self.current_level = "Background"
                        self.level_time = 0
                        self.running = self.choose_next_process()
                    else:
                        self.level_time = 0
                else: 
                    if len(self.foreground_queue) > 0:
                        if self.running.pid != 0:
                            self.background_queue.append(self.running)
                        self.current_level = "Foreground"
                        self.level_time = 0
                        self.running = self.choose_next_process()
                    else:
                        self.level_time = 0
        
        return self.running.pid