"""
    This module defines a class for task fetch stage
    of the Hardware Task Scheduler (HTS)
"""

import sys

class TaskFetch:

    """

    class for fetching tasks

    An instance of this class is meant to be placed after task stream obtained
    from the CPU. It contains a buffer to store tasks to be decoded. It maintains
    program order. We can more functionality later.

    Attributes:
        buffer: A list to store tasks
        count: An integer count of the tasks
    """

    def __init__(self, buffer_size):
        """ Initialize attributes

        Args:
            buffer_size: capacity of the stage, also acts as the looping window size
            because that is the extent to which we can access back instructions

        Returns:
            None
        """
        self.buffer_size = buffer_size
        self.buffer = [None] * buffer_size
        self.max_jump_size = 5 # NOTE change as necessary
        self.tail = 0 # end towards the task stream
        self.pc = 0 # program counter (end towards task decode)
        self.head = 0
        self.task = None  # Input
        self.task_retrieved = None  # Output task
        self.task_valid_o = 0     # Output valid

    def run_cycle(self, task_tuple, pc_tuple, decode_ready, clear_buffer):
        """
        This runs a cycle for the fetch unit.
        Each cycle can have a task coming in and can have one or more
        tasks going out

        Args:
            task_tuple: task got from fetch stage
            pc_tuple: pc_new got from decode/dispatch stage
            decode_ready: is decode stage ready to receive a new task
            clear_buffer: should we persist with current tasks for loop

        Returns:
            None
        """

        # If there is a PC given by the Dispatch unit, use it as PC, else use the current PC
        # and then increment it.
        # Gets the new PC value and a valid signal
        if(pc_tuple[1]):
            pc_current = pc_tuple[0]
            self.pc = pc_tuple[0]
        else:
            pc_current = self.pc

        fetch_ready = self.pc != self.tail 

        if(decode_ready and fetch_ready):
            task_to_return = (self.retrieve_task(pc_current), 1)
            self.pc = self.get_next_ptr(self.pc,1)
        else:
            task_to_return = (None, 0)


        #A new task comes only if the fetch unit asserted ready, so accept it.
        # Writes to next tail
        if(task_tuple[1]):
            self.add_task(task_tuple[0])

            #Calculate the next tail (write pointer)
            self.tail = self.get_next_ptr(self.tail,1)

        # Update the head if the difference between the current PC and head exceeds the maximum jump_width
        # NOTE: Currently cleared tasks can not be fetched again. But in future, this should be supported by
        # making the Task Scheduler a master on the interconnect.
        self.update_head()


        return (task_to_return, self.pc)

    def add_task(self, task):
        """

        Add a task into the TaskFetch stage

        """
        self.buffer[self.tail] = task

        return None

    def retrieve_task(self, pc):
        """
        Returns a task from the queue.

        """
        return self.buffer[pc]

    def ready(self):
        """
        Returns a bool based on the status of the buffer

        Returns:
            False: failure
            True: success
        """
        # If the next tail pointer overwrites the head, then return false. 
        if(self.get_next_ptr(self.tail, 1) == self.head):
            return False 
        else:
            return True 

    def get_next_ptr(self, ptr, incr):
        """
        Get the next pointer. Wrap around if the pointer exceeds the size of the buffer
        """
        if((ptr+incr) > self.buffer_size-1):
            return (ptr+incr) - self.buffer_size
        else:
            return ptr+incr 

    def update_head(self):
        """
        Move head ahead to make space to get more tasks.
        """

        #First calculate the difference between current PC and the head.
        if(self.head <= self.pc):
            difference = self.pc - self.head 
        else:
            difference = self.pc + (self.buffer_size - self.head) 

        # if the difference is bigger than the maximum jump width, overwrite
        if(difference > 2 * self.max_jump_size):
            self.head = self.get_next_ptr(self.head, self.max_jump_size)

    def log_state(self):
        """ Export state of stage

        Args:
            None

        Returns:
            None
        """
        print("state : ", list(self.buffer))
        print("PC : ", self.pc)
        print("head: " + str(self.head) + ", tail : " + str(self.tail))
        print("ready " + str(self.ready()))


# Test the fetch stage
if __name__ == '__main__':

        fetch = TaskFetch(20)

        print("\n CYCLE 1")
        if(fetch.ready()):
            # add a cycle and don't read out a task
            print(fetch.run_cycle(('t1', 1),(2, 0), 1, 1))

        fetch.log_state()

        print("\n CYCLE 2")
        if(fetch.ready()):
            # add a cycle and don't read out a task
            print(fetch.run_cycle(('t2', 1),(2, 0), 1, 1))

        fetch.log_state()

        print("\n CYCLE 3")
        if(fetch.ready()):
            # add a cycle and don't read out a task
            print(fetch.run_cycle(('t3', 1),(2, 0), 0, 1))

        fetch.log_state()

        print("\n CYCLE 4")
        if(fetch.ready()):
            # add a cycle and don't read out a task
            print(fetch.run_cycle(('t2', 1),(0, 1), 1, 1))

        fetch.log_state()

        for i in range(15):
            print("\n CYCLE " + str( i+5))
            if(fetch.ready()):
                # add a cycle and don't read out a task
                print(fetch.run_cycle(('t2', 1),(0, 0), 1, 1))
            else:
                print(fetch.run_cycle(('t2', 0),(0, 0), 1, 1))
            fetch.log_state()
