# Module object to detect dependency between tasks
# Dependency lies when their memory regions overlap

import copy

class resolve_dependency:

    def __init__(self):
        self.task1 = None
        self.task2 = None
        self.is_dependent = False
        self.result = None
    

    def run_cycle(self, task1, task2, valid):
        if (valid):
            self.task1 = task1
            self.task2 = task2
            self.is_dependent = False
            self.check_dependency()
            self.result = True
        else:
            self.is_dependent = False
            self.result = None

        return(self.result, self.is_dependent)
    
    
    # Checks for dependency
    # Accepts two task objects
    # Returs True if their memory region overlap, else False
    def check_dependency(self):

        # Sort the tasks based on start mem_address
        if (task1['out_mem'] <= task2['inp_mem']):
            first_task = copy.deepcopy(self.task1)
            sec_task = copy.deepcopy(self.task2)
        else:
            first_task = copy.deepcopy(task2)
            sec_task = copy.deepcopy(task1)
    
        task1_inp_start = first_task['inp_mem']
        task2_inp_start = sec_task['inp_mem']
        task1_inp_end   = first_task['inp_mem'] + first_task['inp_size']
        task2_inp_end   = sec_task['inp_mem']   + sec_task['inp_size']
        task1_out_start = first_task['out_mem']
        task2_out_start = sec_task['out_mem']
        task1_out_end   = first_task['out_mem'] + first_task['out_size']
        task2_out_end   = sec_task['out_mem'] + sec_task['out_size']

        # Now check for overlap
        if (task1_out_end >= task2_inp_end):
            self.is_dependent = True
        elif (task1_out_end >= task2_inp_start):
            self.is_dependent = True
        else:
            self.is_dependent = False


if __name__ == "__main__":
    task1 = { 'accelerator'    : "FFT",
                        'inp_mem'   : 0,
                        'inp_size'  : 1800,
                        'out_mem'   : 2000,
                        'out_size'  : 1000,
                        'task_id'   : 0,
                        'pid'       : 0
                        }
    task2 = { 'accelerator'    : "FFT",
                        'inp_mem'   : 2200,
                        'inp_size'  : 1800,
                        'out_mem'   : 4000,
                        'out_size'  : 1000,
                        'task_id'   : 1,
                        'pid'       : 0
                        }
    resolve = resolve_dependency()
    result, dependency = resolve.run_cycle(task1, task2, True)
    print(result, dependency)
