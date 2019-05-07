"""
    This module takes in a task and returns the decoded task

    You can instantiate by calling decoder(task_length)

    Task structure:

    Total               - 128 bit
    Supported max DRAM  - 4GB
    Min Block Size      - 64kB
    Max allocable blocks- 256
    Max allocable Size  - 8MB

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
    [23:8]  src0
    [39:24] src1
    [55:40] dst0
    [63:56] control - Optional

"""

import sys

import accelerators

class TaskDecode:

    def __init__(self, task_len):
        self.task       = '0' * task_len
        self.task_len   = task_len
        self.task_dict  = {}
        self.task_id = 0
        self.task_id_max = 1024*1024

    def run_cycle(self, task_tuple):
        task = task_tuple[0]
        task_valid = task_tuple[1]

        self.task   = str(task)
        flag        = False

        if(task_valid):
            flag = self.decode()

            # Decode success and input was valid
            if(flag):
                return (self.task_dict, 1)

            else:
                # Decode failed
                sys.exit("Invalid unidentified task: %s" % (self.task))
        # Input was not valid, return the output valid to be 0
        else:
            return (None, 0)

    def decode(self):

        # First check whether the instruction format is for CPU/TFU
        instr = accelerators.instr_decode[int(self.task[0:2], 16)]

        if(instr in accelerators.iTFU):
            #Since each field is atleast 4 bits, we don't need binary rep
            acc_id      = self.task[0:2]
            inp0_mem    = self.task[2:10]
            inp0_size   = self.task[10:12]
            inp1_mem    = self.task[12:20]
            inp1_size   = self.task[20:22]
            out_mem     = self.task[22:30]
            out_size    = self.task[30:32]
            control     = self.task[32:34]

            #TEMP task id is local
            self.task_id= self.task_id + 1 if ((self.task_id + 1) < self.task_id_max) else 0
            task_id     = str(self.task_id)

            # populate the task dict
            self.task_dict   = {'accelerator'   : instr,
                                'inp0_mem'      : int(inp0_mem,16),
                                'inp0_size'     : int(inp0_size,16),
                                'inp1_mem'      : int(inp1_mem,16),
                                'inp1_size'     : int(inp1_size,16),
                                'out0_mem'       : int(out_mem,16),
                                'out0_size'      : int(out_size,16),
                                'task_id'       : task_id,
                                'control'       : int(control,16),
                                'instrType'     : 'TFU'
                            }

            return True

        elif(instr in accelerators.iCPU):

            src0 = self.task[2:10]
            src1 = self.task[10:18]
            dst0 = self.task[18:26]
            control = self.task[26:28]

            #TEMP task id is local
            self.task_id= self.task_id + 1 if ((self.task_id + 1) < self.task_id_max) else 0
            task_id     = str(self.task_id)

            # populate the task dict
            self.task_dict   = {'accelerator'  : instr,
                                'src0'         : int(src0,16),
                                'src1'         : int(src1,16),
                                'dst0'          : int(dst0,16),
                                'control'       : int(control,16),
                                'task_id'       : task_id,
                                'instrType'     : 'CPU'
                               }

            return True

        else:
            # Unidentified instruction
            return False

if __name__ == '__main__':

    decoder_hts = TaskDecode(16)
    print(decoder_hts.run_cycle(('1000R000R100R200', 1)))
    print(decoder_hts.run_cycle(('1000R000R100R200', 0)))
    print(decoder_hts.run_cycle(('06000000000000000000123123123', 1)))
