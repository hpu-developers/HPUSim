"""
    This file defines a reservation station.

    Its main job is to maintain a queue of jobs and dispatch the jobs to the
    accelerators as soon as the dependencies are resolved.

"""

from acc_status import AccStatus
from accelerators import *

class ResStation:

    def __init__(self, accelerator, size):

        self.accelerator = accelerator
        self.size        = size

        # Stores the information about the task
        self.data       = dict() # Key - task id, Value - operands (in and out)
        # Keep the task dict here
        self.memory     = dict()
        # 1 refers to the correspoding task being ready
        self.ready      = dict() # Key - task id, Value - task ready
        # To track the dependency
        self.dependency = dict() # Key - task_id, Value - out_mem
        # To decode the dependencies
        self.waiting_for = dict()

        # Push task
        self.push_task = None # Decoded task ID
        self.push_valid = 0
        self.pushAccID    = None # ID of the FU

    def run_cycle(self, task, CDB, AccStatus, task_to_abort):

        """
            This attribute takes in 3 inputs

                1. task - the entire task dictionary produced from the decode stage with dependency field added
                        dependency - This is returned from MemoryTrack (task_dispatch)
                    - (decoded_task, dependent_task_id, valid)
                2. CDB - this is the broadcast bus that is being monitored to resolve any dependency
                    - (accelerator, acc_id, task_id, result, valid)

                3. AccStatus - This is an object that returns the status of the accelerators

                4. Task to abort - This deletes any waiting task (None, 0) TODO

            Returns:
                Task to send out to FU (task_dict, valid), acc_id for the task

        """
        # New incoming task
        # valid task
        # if the task is valid, push it into the memory
        # Add entries to dependency tables if needed

        # Expand the bus
        task_dict, operands, task_valid = task
        CDB_accelerator, CDB_accID,CDB_taskID,result,dest,CDB_valid = CDB
        self.acc_status = AccStatus # Object
        self.CDB = CDB


        # 1. Adding to RS
        if(task_valid):
            self.task = task_dict
            self.operands = operands # specifies the task_id on which the task is dependent
            if(task_dict['accelerator'] == self.accelerator):
                self.update_rs()

        # 2. Dispatch from RS
        # If there is any task that can be pushed to the accelerator
        # and the accelerator is not busy, then send it
        self.send_task()

        # 3. Clear from RS
        # If there are messages on the CDB, update RS if required
        if(CDB[5]):
            self.clear_dependency()

        return (self.push_task,  self.push_valid) , self.pushAccID

    def send_task(self):

        """
            This attribute checks if there is any task that has its dependencies cleared.
            If found, it will be pushed to the corresponding accelerator
        """

        self.push_task = None
        self.pushAccID = None
        self.push_valid = 0

        # If the accelerator is free and there is a task to send, let's do so
        isTaskReady = 1 in self.ready.values()

        # Check if accelerators are free
        isAccReady = False
        pushAccID  = None
        acc_IDs = accelerators[self.accelerator]['ID']
        for accID in acc_IDs:
            if(self.acc_status.check_status(accID) == 0):
                isAccReady = True
                pushAccID = accID
                break

        # Both conditions satisfy
        if(isTaskReady and isAccReady):
            # This is O(n) here, would be O(1) in hardware
            for key in self.ready:
                if(self.ready[key] == 1):
                    # Create the task to push to FU and break
                    self.push_task = self.memory[key]
                    self.push_task['data'] = self.data[key]
                    # debug
                    print("--- IN RES STATION -- task['data'] -> ", self.push_task['data'])
                    self.pushAccID = pushAccID
                    self.push_valid = 1
                    # Remove the entries
                    self.data.pop(key)
                    self.memory.pop(key)
                    self.ready.pop(key)
                    break

        return None

    def update_rs(self):
        """
            This attribute pushes the task into RS
        """

        # Decode the task
        task_id = self.task['task_id']
        in_operands = self.operands['in']
        out_operands = self.operands['out']

        # This is what goes to FUs
        self.data[task_id] = {'in':[None]*len(in_operands), 'out':out_operands}
        self.memory[task_id] = self.task

        # Check if there any dependencies
        if(any(zip(*in_operands)[0])):
            # Go through input operands to check for dependencies
            self.dependency[task_id] = []
            for idx, (isDependent,tid) in enumerate(in_operands):
                # We update a watcher for task completion and also update the dependency
                if(isDependent):
                    # Key: Current task ID, Value: Dependent task ID (Do not add duplicates)
                    if((tid,idx) not in self.dependency[task_id]):
                        self.dependency[task_id].append((tid, idx))
                    # Key: Task ID, value: All the tasks waiting for (do not add duplicates)
                    if(tid in self.waiting_for):
                        if(task_id not in self.waiting_for[tid]):
                            self.waiting_for[tid].append(task_id)
                    else:
                        self.waiting_for[tid] = [task_id]
                else:
                    self.data[task_id]['in'][idx] = tid
            self.ready[task_id]    = 0
        else:
            # Populate the data
            for idx, (isDependent,tid) in enumerate(in_operands):
                self.data[task_id]['in'][idx] = tid
            self.ready[task_id]     = 1

        return None

    def clear_dependency(self):

        """
            Based on the CDB broadcast, update the dependency table
        """

        CDB_accelerator, CDB_accID,CDB_taskID,result,dest,CDB_valid = self.CDB

        # If there is a task waiting for this
        if(CDB_valid):
            # Get all the tasks that are waiting for this
            if(CDB_taskID in self.waiting_for):
                update_tasks = self.waiting_for[CDB_taskID]
                # Clear the dependencies
                for update_taskID in update_tasks:
                    updated_dependency = []
                    # Go through the operands
                    for tid, idx in self.dependency[update_taskID]:
                        if(tid == CDB_taskID):
                            self.data[update_taskID]['in'][idx] = result
                        else:
                            updated_dependency.append((tid, idx))

                    # in case it clears everything, get this task ready
                    if(len(updated_dependency) == 0):
                        self.ready[update_taskID] = 1
                        del(self.dependency[update_taskID])
                    # Otherwise retain the updated list
                    else:
                        self.dependency[update_taskID] = updated_dependency

                # Now remove all the dependencies related to this task
                del(self.waiting_for[CDB_taskID])

    def rs_ready(self):
        """
            Make sure the RS memory is not at its max
        """
        if(len(self.memory) == self.size):
            return False
        else:
            return True

    def log_state(self):
        """
            Print the contents for debug purposes
        """

        print("\n Status of the Reservation status for %s" % self.accelerator)
        if(self.memory):
            print(" Memory : " + str(self.memory))
        if(self.dependency):
            print(" Dependency: " + str(self.dependency))
        if(self.ready):
            print(" Ready: " + str(self.ready))
        if(self.waiting_for):
            print(" Waiting for ", self.waiting_for)
        #print("\n")
