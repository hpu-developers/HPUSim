#!/usr/bin/env python

"""
    This module defines a class for creating a task stream
    of the Hardware Task Scheduler (HTS)

    It needs apps.asm file to produce the stream.

    OPCODE Format for TFUs

    [7:0]   Acc ID
    [23:8]  Input0 memory
    [31:24] Input0 Size
    [47:32] Input1 memory
    [55:48] Input1 Size
    [71:56] Output memory
    [79:72] Output size
    [87:80] Control - Optional
    [95:88] Task ID - Optional
    [99:96] Process ID - Optional

    OPCODE Format for CPU

    [7:0]   Instr ID
    [39:8]  src0
    [71:40] src1
    [95:72] dst0
    [103:96] control
"""

import sys,os

is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as queue
else:
    import queue as queue

BASE = os.environ['BASE']
sys.path.insert(0, BASE+'/DUT/')

import random as random
import accelerators

class Parse:

    """
    Class for Parse tasks

    It parses the tasks and gives a functionality to pop the tasks one by one.
    It maintains program order.

    Attributes:
    buffer: A FIFO queue to store tasks
    count: An integer count of the tasks
    """

    def __init__(self, filepath):
        """ Initialize attributes

        Args:
            buffer_size: capacity of the stage

        Returns:
            None
        """

        # Load the task file
        task_list = get_task_list(filepath)

        buffer_size = len(task_list)
        self.buffer = queue.Queue(maxsize=buffer_size)

        # Load the all task commands into the buffer
        list = [self.buffer.put(task) for task in task_list]

        self.count = 0

    def get_task(self):
        """ Get one task from the stream

        Args:
            None

        Returns:
            0: failure
            task: returns one task based on FIFO
        """
        if self.buffer.empty() is True:
            return (None, 0)
        else:
            return (self.buffer.get(), 1)

    def log_state(self):
        """ Export state of stage
        Args:
            None

        Returns:
            None
        """
        print("TaskStream : ", list(self.buffer.queue))

# Other Functions to read the ASM
def get_task_list(filepath):
    """
        Reads the code and returns machine level code.
    """

    task_file = open(filepath, 'r')
    task_list = task_file.readlines()

    # Remove the comments:
    task_list_no_comments = list()
    for task in task_list:
        if((';' not in task) and (task.rstrip())):
            task_list_no_comments.append(task)

    # Convert the tasks into understandable format
    task_list = [convert_format(task) for task in task_list_no_comments]

    return task_list

def convert_format(task):

    task_fields = task.rstrip().split(" ")

    print(task_fields)

    # Check whether the instruction is a CPU instruction or TFU instruction.

    if(task_fields[0] in accelerators.iTFU):

        assert len(task_fields)>=7, "Unexpected length in TFU OPCODE {0}".format(task)

        # Get the code into hex format
        acc_id      = hex(accelerators.instr_encode[task_fields[0]])[2:].zfill(2)

        control = 0

        # Input 0
        inp0_mem    = task_fields[1][1:].zfill(8)
        if(task_fields[1][0] == 'R'):
            control += 0x1
        inp0_size   = task_fields[2][1:].zfill(2)
        if(task_fields[2][0] == 'R'):
            control += 0x2
        inp1_mem    = task_fields[3][1:].zfill(8)
        if(task_fields[3][0] == 'R'):
            control += 0x4
        inp1_size   = task_fields[4][1:].zfill(2)
        if(task_fields[4][0] == 'R'):
            control += 0x8
        out_mem     = task_fields[5][1:].zfill(8)
        if(task_fields[5][0] == 'R'):
            control += 0x10
        out_size    = task_fields[6][1:].zfill(2)
        if(task_fields[6][0] == 'R'):
            control += 0x20

        control = hex(control)[2:].zfill(2)

        return (acc_id + inp0_mem + inp0_size + inp1_mem + inp1_size + out_mem + out_size + control)

    elif(task_fields[0] in accelerators.iCPU):
        # Get the code into hex format

        acc_id      = hex(accelerators.instr_encode[task_fields[0]])[2:].zfill(2)

        # We check some conditions to support decoding later
        # 1. Check if each one is a register or immediate
        # 2. Check if each one have a sign bit
        control = 0

        # SRC 0
        if(len(task_fields)>1):
            if(task_fields[1][1]=='-'):
                src0        = task_fields[1][2:].zfill(8)
            else:
                src0        = task_fields[1][1:].zfill(8)

            if(task_fields[1][0] == 'R'):
                control += 0x1
            if(task_fields[1][1] == '-'):
                control += 0x10
        else:
            src0    = '00000000'

        # SRC 1
        if(len(task_fields)>2):
            if(task_fields[2][1]=='-'):
                src1        = task_fields[2][2:].zfill(8)
            else:
                src1        = task_fields[2][1:].zfill(8)

            if(task_fields[2][0] == 'R'):
                control += 0x2
            if(task_fields[2][1] == '-'):
                control += 0x20
        else:
            src1    = '00000000'

        # DST 0
        if(len(task_fields)>3):
            if(task_fields[3][1]=='-'):
                dst0        = task_fields[3][2:].zfill(8)
            else:
                dst0        = task_fields[3][1:].zfill(8)

            if(task_fields[3][0] == 'R'):
                control += 0x4
            if(task_fields[2][1] == '-'):
                control += 0x40
        else:
            dst0    = '00000000'

        control = hex(control)[2:].zfill(2)

        return (acc_id + src0 + src1 + dst0 + control)

    else:
        print("Unidentified instruction {0}".format(task_fields[0]))
        sys.exit()


# Test
if __name__ == '__main__':

    stream_1 = Parse(BASE + '/testbench/tests/sanity/testParser.asm')
    stream_1.log_state()
