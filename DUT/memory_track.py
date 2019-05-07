"""
    This block keeps a track of all the memory regions
    that each of the task is working on.

    The entries can have the following state:

    EXPECT: The data is being produced by someone
    CLEAR : The requested entry is absent --> can be simply read from the block
    Following actions can be requested:

    CREATE: creates an entry in the EXPECT state
    REQUEST: requests for a memory

"""
import accelerators
import sys

class MemoryTrack:

    def __init__(self, window):

        """
            Size: the maximum number of memory regions tracked
        """
        self.window = window
        self.memory = {} # Key - out_mem, value - task_id
        # (task_ID, valid)
        self.block_return = (None, None)

    def run_cycle(self,CDB, dispatch_req, dispatch_info):
        """
        Inputs:
        CDB - has six fields (1) Accelerator (2) acc_id (3) task_id (4) Result (5) Destination (6) Valid
        dispatch_req - has 3 fields (1) task_id (2) memory block (3) valid
        dipsatch_inf - has 3 fields (1) task_id (2) memory block (3) valid
        """

        # Update all the local regs
        self.CDB = CDB
        self.dispatch_info = dispatch_info
        self.dispatch_req = dispatch_req
        self.block_return = (None, 0)

        # If a task is requesting memory
        if(dispatch_req[2]):
            self.mem_req()

        # If CDB has a valid message, update the tables
        if(CDB[5] and (CDB[0] in accelerators.iTFU)):
            self.mem_update()

        # if a task is informing that it'll update some block
        # NOTE: The assumption here is that there will be no WAW, WAR hazards
        if(dispatch_info[2]):
            self.mem_reserve()


        return self.block_return


    def mem_update(self):
        """
            This is when there is a CDB broadcast that some accelerator finished its work
        """

        #Simply remove that block from the tracker
        print("DEBUG MEM", self.memory)
        # check if the task ID is in the memory
        clear_key = None
        if(self.CDB[3] in self.memory):
            del self.memory[self.CDB[3]][0]
            if(len(self.memory[self.CDB[3]]) == 0):
                self.memory.pop(self.CDB[3], None)
        else:
            sys.exit("Key not found in MemTrack for CDB packet " + str(self.CDB))

    def mem_reserve(self):
        """
        This is when someone informs that they will be writing their
        outputs there.
        """
        #NOTE: assuming there will be no WAW, WAR hazards
        # Save the infomration on the accelerator that will be writing the output back to this location
        if(self.dispatch_info[1] in self.memory):
            self.memory[self.dispatch_info[1]].append(self.dispatch_info[0])
        else:
            self.memory[self.dispatch_info[1]] = [self.dispatch_info[0]]

    def mem_req(self):

        """
        This is when someone requests for a block

        """

        # Check if the requested block exists
        # if it does --> the memory will be written by someone
        # Else return CLEAR
        if(self.dispatch_req[1] in self.memory.keys()):
            self.block_return = (self.memory[self.dispatch_req[1]][-1], 1)
        else:
            self.block_return = (None, 1)

    def check_mem_size(self):
        """
            Make sure the dictionary size does not icrease over the limit
        """
        if(len(self.memory) > self.window):
            print("WARNING: Exceeded the Tracker window")
            return False
        else:
            return True

    def log_state(self):
        """
            Prints the state of the memory
        """

        print(self.memory)

## Test

if __name__ == '__main__':

    track = MemoryTrack(4)
    CDB = (None, None, None, None, None, False)
    track.log_state()
    print(track.run_cycle(CDB, (0,0,0), ('fft', 123, 1)))
    track.log_state()
    print(track.run_cycle(CDB, ('fft', 123, 1), (0,0,0)))
    track.log_state()
    print(track.run_cycle(CDB, ('fft', 124, 1), (0,0,0)))
    track.log_state()
    CDB = ('fft', None, None, None, 123, True)
    print(track.run_cycle(CDB, (0,0,0), (0,0,0)))
    track.log_state()

