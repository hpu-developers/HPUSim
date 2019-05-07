"""
    This block keeps a track of all the registers
    that each of the task is working on.

    The entries can have the following state:

    EXPECT: The data is being produced by someone
    CLEAR : The requested entry is absent --> can be simply read from the block
    Following actions can be requested:

    CREATE: creates an entry in the EXPECT state
    REQUEST: requests for a memory

"""
import accelerators

class regTrack:

    def __init__(self):

        """
            Size: the maximum number of registers tracked (Not implemented here, only in hardware)
        """

        self.memory = {} # Key - out_reg, value - task_id (producer)
        # (task_ID, valid)
        self.block_return = (None, None)

    def run_cycle(self,CDB, regFile, dispatch_req, dispatch_info):
        """
            Inputs:
            CDB - Has Six fileds (1) Accelerator (2) acc_id (3) task_id (4) Result (5) Dest (6) Valid
            RegFile - The register file
            dispatch_req - has 3 fields (1) task_id (2) register (3) valid
            dipsatch_inf - has 3 fields (1) task_id (2) register (3) valid
        """

        # Update all the local regs
        self.CDB = CDB
        self.dispatch_info = dispatch_info
        self.dispatch_req = dispatch_req
        self.regFile = regFile
        self.block_return = (None, 0)

        # If a task is requesting memory
        if(dispatch_req[2]):
            self.reg_req()

        # If CDB has a valid message, update the tables
        if(CDB[5] and (CDB[0] in accelerators.iCPU)):
            self.reg_update()

        # if a task is informing that it'll update some block
        # NOTE: The assumption here is that there will be no WAW, WAR hazards
        if(dispatch_info[2]):
            self.reg_reserve()


        return self.block_return


    def reg_update(self):
        """
            This is when there is a CDB broadcast that some accelerator finished its work
        """

        #Simply remove that block from the tracker, and update the regfile
        accelerator, accID, taskID, result, dest, _ = self.CDB

        # check if the task ID is in the memory
        clear_key = None
        if(dest in self.memory):
            # TODO: Do in-order commit
            # assert self.memory[dest][0] == taskID, "WAW hazard"

            # Remove the entry
            self.memory[dest].remove(taskID)

            # if the list is emty, we remove the dest altogether
            if(len(self.memory[dest])==0):
                del(self.memory[dest])

            # Updates the regfile with the correct value
            self.regFile.write(dest,result)
        else:
            print("WARNING: {0} instruction is finishing without updating dest location".format(self.CDB[0]))

    def reg_reserve(self):
        """
        This is when someone informs that they will be writing their
        outputs there.
        """
        #NOTE: assuming there will be no WAW, WAR hazards
        # Save the infomration on the accelerator that will be writing the output back to this location
        taskID, register, _ = self.dispatch_info
        if(register in self.memory):
            self.memory[register].append(taskID)
        else:
            self.memory[register] = [taskID]

    def reg_req(self):

        """
            This is when someone requests for a block
        """
        # Check if the requested block exists
        # if it does --> the memory will be written by someone
        # Else return CLEAR
        taskID, register, _ = self.dispatch_req

        if(register in self.memory.keys()):
            self.block_return = (self.memory[register][-1], 1)
        else:
            self.block_return = (None, 1)

    def log_state(self):
        """
            Prints the state of the memory
        """

        print(self.memory)

## Test

if __name__ == '__main__':

    import sys,os
    BASE = os.environ['BASE']
    sys.path.insert(0, BASE+'/testbench/')
    sys.path.insert(0, BASE+'/utils/')
    import regfile

    track = regTrack()
    regFile = regfile.RegFile(16)

    # Create an entry
    _ = track.run_cycle((0,0,0,0,0,0), regFile, (0,0,0), (12,2, 1))

    # Check if the entry is returned
    task, valid = track.run_cycle((0,0,0,0,0,0), regFile, (15, 2, 1), (0,0,0))

    if((task,valid) != (12,1)):
        print("TEST FAILED - 0")
        sys.exit()

    # This should not have any problem (checking reg 2)
    task, valid = track.run_cycle((0,0,0,0,0,0), regFile, (14, 3, 1), (0,0,0))

    if((task,valid) != (None,1)):
        print("TEST FAILED - 1")
        sys.exit()

    _ = track.run_cycle(('mov',1, 12, 0xdeadbeef, 2, 1), regFile, (0,0,0), (0,0,0))

    val = regFile.read(2)

    if(val != 0xdeadbeef):
        print("TEST FAILED - 2")
        sys.exit()

    print("TEST PASSED")

