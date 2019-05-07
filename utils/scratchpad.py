"""
    This is a controller that instantiates a buffet core and builds a wrapper
    around it to make it programmable. This is exposed to the programmer.

    The function calls accepted:
        allocate    <src> <dummy> <size>
        load        <src> <dst> <size>
        store       <src> <dst> <size>
        shrink      <src> <dummy> <size>
        routine     <dummy> <dummy> <dummy>
"""
import Queue
import sys
from buffet import buffet

class scratchpad:

    def __init__(self, size):

        self.bank = buffet(size)
        self.read_queue_0 = Queue.Queue()
        self.update_queue_0 = Queue.Queue()
        self.read_queue_1 = Queue.Queue()
        self.write_queue_0 = Queue.Queue(maxsize=2)
        self.write_queue_1 = Queue.Queue(maxsize=2)

    def run_cycle(self, read_channel0, update_channel0, write_channel0, read_channel1, write_channel1, alloc_channel, shrink_channel):
        """
            This is the main function to call the read/write request.
        """
        # Inputs
        araddr0, arvalid0 = read_channel0
        waddr0, wdata0, wvalid0 = write_channel0
        uaddr0, udata0, uvalid0 = update_channel0
        araddr1, arvalid1 = read_channel1
        waddr1, wdata1, wvalid1 = write_channel1
        shrink_addr, shrink_valid = shrink_channel
        alloc_addr, alloc_size, is_free, alloc_valid = alloc_channel

        # Outputs
        rdata0 = 0
        rvalid0 = 0
        readID0 = None
        rdata1 = 0
        rvalid1 = 0
        readID1 = None
        shrink_resp = 0
        alloc_resp = 0

        # We will update the scratchpad every cycle to check if there are
        # any outstanding reads to be read
        self.bank.moveOutstandingReads()

        ######### CHANNEL 0-1 ######### 

        #### WRITE ####

        # If there were any write requests pending in the queue, complete them.
        if(not self.write_queue_0.empty()):
            self.bank.write(*self.write_queue_0.get())
        if(not self.write_queue_1.empty()):
            self.bank.write(*self.write_queue_1.get())

        # Load the write requests into the queue
        if(wvalid0):
            self.write_queue_0.put((waddr0, wdata0))
        if(wvalid1):
            self.write_queue_1.put((waddr1, wdata1))

        #### UPDATE ####

        # Add a cycle delay
        if(not self.update_queue_0.empty()):
            self.bank.update(*self.update_queue_0.get())
        if(uvalid0):
            self.update_queue_0.put((uaddr0, udata0))

        #### READ ####

        # If there are some outstanding reads to be completed then they get priority.
        if(self.bank.checkReadyReads()):
            _, readDataOutstanding, readID, readIDOutstanding = self.bank.clearReadyRead()

            if(readIDOutstanding == 0):
                rvalid0, rdata0, readID0 = 1, readDataOutstanding, readID
            elif(readIDOutstanding == 1):
                rvalid1, rdata1, readID1 = 1, readDataOutstanding, readID

            # Based on the readID, we will only consider reads from the other channels
            if((readIDOutstanding !=0) and (not self.read_queue_0.empty())):
                rvalid0, rdata0, readID0, _ = self.bank.read(*self.read_queue_0.get())
            if((readIDOutstanding !=1) and (not self.read_queue_1.empty())):
                rvalid1, rdata1, readID1, _ = self.bank.read(*self.read_queue_1.get())

        else:
            # Pop read requests if any
            if(not self.read_queue_0.empty()):
                rvalid0, rdata0, readID0, _  = self.bank.read(*self.read_queue_0.get())
            if(not self.read_queue_1.empty()):
                rvalid1, rdata1, readID1, _ = self.bank.read(*self.read_queue_1.get())

        # Push requests to the queue
        if(arvalid0):
            self.read_queue_0.put((araddr0, 0))
        if(arvalid1):
            self.read_queue_1.put((araddr1,1))

        #### Shrink ####

        # If there is a shrink request, we accept. TODO: perform some checks
        if(shrink_valid):
            shrink_resp = self.bank.shrink(shrink_addr)

        #### Allocate ####

        # If there is a allocate request, we accept. TODO: perform some checks
        if(alloc_valid):
            if(is_free):
                alloc_resp = self.bank.free(alloc_addr)
            else:
                alloc_resp = self.bank.allocate(alloc_addr, alloc_size)


        ################# Response #################
        # Combine results and respond
        read_resp_channel0 = readID0, rdata0, rvalid0
        read_resp_channel1 = readID1, rdata1, rvalid1
        shrink_resp_channel = shrink_resp
        alloc_resp_channel = alloc_resp

        # print("Read Queue 0", list(self.read_queue_0.queue))
        # print("Read Queue 1", list(self.read_queue_1.queue))
        # print("Write Queue 0", list(self.write_queue_0.queue))
        # print("Write Queue 1", list(self.write_queue_1.queue))

        return read_resp_channel0, read_resp_channel1, shrink_resp_channel, alloc_resp_channel


if __name__ == "__main__":

    # Instantiate a scratchpad
    spad = scratchpad(128)

    # Allocate something

    read_channel0 = 0,0
    read_channel1 = 0,0
    update_channel0 = 0,0,0
    write_channel0 = 0,0,0
    write_channel1 = 0,0,0
    shrink_channel = 0,0
    alloc_channel = 0, 16, 0, 1

    read_resp_channel0, read_resp_channel1, shrink_resp_channel, alloc_resp_channel = spad.run_cycle(read_channel0, update_channel0, write_channel0, read_channel1, write_channel1, alloc_channel, shrink_channel)
    print("Cycle 1")
    print("READ RESP CHANNEL0 (ID, DATA, VALID): ",read_resp_channel0)
    print("READ RESP CHANNEL1 (ID, DATA, VALID): ",read_resp_channel1)
    print("SHRINK RESP CHANNEL (VALID): ",shrink_resp_channel)
    print("ALLOC RESP CHANNEL (VALID): ",alloc_resp_channel)
    if(alloc_resp_channel != True):
        print("TEST FAILED, expected alloc response")
        sys.exit()
    print("\n-----------------------------\n\n")

    # Write Something, and we will also try to read a data that is not present (fine grained sync)
    read_channel0 = 2,1
    read_channel1 = 0,0
    update_channel0 = 0,0,0
    write_channel0 = 0,0xdeadbeef,1
    write_channel1 = 0,0xdeadbeef,1
    shrink_channel = 0,0
    alloc_channel = 0, 0,0, 0

    read_resp_channel0, read_resp_channel1, shrink_resp_channel, alloc_resp_channel = spad.run_cycle(read_channel0, update_channel0, write_channel0, read_channel1, write_channel1, alloc_channel, shrink_channel)
    print("Cycle 2")
    print("READ RESP CHANNEL0 (ID, DATA, VALID): ",read_resp_channel0)
    print("READ RESP CHANNEL1 (ID, DATA, VALID): ",read_resp_channel1)
    print("SHRINK RESP CHANNEL (VALID): ",shrink_resp_channel)
    print("ALLOC RESP CHANNEL (VALID): ",alloc_resp_channel)
    print("\n-----------------------------\n\n")

    # Read the data (valid data) - Also we write to addr 2
    read_channel0 = 0,1
    read_channel1 = 1,1
    update_channel0 = 0,0,0
    write_channel0 = 0,0,0
    write_channel1 = 0,0xdeadbeef,1
    shrink_channel = 0,0
    alloc_channel = 0, 0, 0, 0

    read_resp_channel0, read_resp_channel1, shrink_resp_channel, alloc_resp_channel = spad.run_cycle(read_channel0, update_channel0, write_channel0, read_channel1, write_channel1, alloc_channel, shrink_channel)
    print("Cycle 3")
    print("READ RESP CHANNEL0 (ID, DATA, VALID): ",read_resp_channel0)
    print("READ RESP CHANNEL1 (ID, DATA, VALID): ",read_resp_channel1)
    print("SHRINK RESP CHANNEL (VALID): ",shrink_resp_channel)
    print("ALLOC RESP CHANNEL (VALID): ",alloc_resp_channel)
    print("\n-----------------------------\n\n")

    # Wait for the outstanding read to complete (we need to see the previous outstanding read on addr 2 complete, and
    # addr 0 also complete)
    # We will apply an update on address 2
    read_channel0 = 0,0
    read_channel1 = 0,0
    update_channel0 = 2,0xbeefdead,1
    write_channel0 = 0,0,0
    write_channel1 = 0,0,0
    shrink_channel = 0,0
    alloc_channel = 0, 0, 0, 0

    read_resp_channel0, read_resp_channel1, shrink_resp_channel, alloc_resp_channel = spad.run_cycle(read_channel0, update_channel0, write_channel0, read_channel1, write_channel1, alloc_channel, shrink_channel)
    print("Cycle 4")
    print("READ RESP CHANNEL0 (ID, DATA, VALID): ",read_resp_channel0)
    print("READ RESP CHANNEL1 (ID, DATA, VALID): ",read_resp_channel1)
    print("SHRINK RESP CHANNEL (VALID): ",shrink_resp_channel)
    print("ALLOC RESP CHANNEL (VALID): ",alloc_resp_channel)
    if(not(read_resp_channel0[2]==1 and read_resp_channel0[0]==2 and read_resp_channel0[1]==0xdeadbeef)):
        print("TEST FAILED, Channel 0 unexpected")
        sys.exit()
    if(not(read_resp_channel1[2]==1 and read_resp_channel1[0]==1 and read_resp_channel1[1]==0xdeadbeef)):
        print("TEST FAILED, Channel 1 unexpected")
        sys.exit()
    print("\n-----------------------------\n\n")

    # Wait for the outstanding read to complete (We need to see read on addr 1 complete here)
    read_channel0 = 2,1
    read_channel1 = 0,0
    update_channel0 = 0,0,0
    write_channel0 = 0,0,0
    write_channel1 = 0,0,0
    shrink_channel = 0,0
    alloc_channel = 0, 0, 0, 0

    read_resp_channel0, read_resp_channel1, shrink_resp_channel, alloc_resp_channel = spad.run_cycle(read_channel0, update_channel0, write_channel0, read_channel1, write_channel1, alloc_channel, shrink_channel)
    print("Cycle 5")
    print("READ RESP CHANNEL0 (ID, DATA, VALID): ",read_resp_channel0)
    print("READ RESP CHANNEL1 (ID, DATA, VALID): ",read_resp_channel1)
    print("SHRINK RESP CHANNEL (VALID): ",shrink_resp_channel)
    print("ALLOC RESP CHANNEL (VALID): ",alloc_resp_channel)
    if(not(read_resp_channel0[2]==1 and read_resp_channel0[0]==0 and read_resp_channel0[1]==0xdeadbeef)):
        print("TEST FAILED, Channel 0 unexpected")
        sys.exit()
    print("\n-----------------------------\n\n")

    #  Shrink the space
    read_channel0 = 0,0
    read_channel1 = 0,0
    update_channel0 = 0,0,0
    write_channel0 = 0,0,0
    write_channel1 = 0,0,0
    shrink_channel = 0,0
    alloc_channel = 0, 0,0, 0

    read_resp_channel0, read_resp_channel1, shrink_resp_channel, alloc_resp_channel = spad.run_cycle(read_channel0, update_channel0, write_channel0, read_channel1, write_channel1, alloc_channel, shrink_channel)
    print("Cycle 6")
    print("READ RESP CHANNEL0 (ID, DATA, VALID): ",read_resp_channel0)
    print("READ RESP CHANNEL1 (ID, DATA, VALID): ",read_resp_channel1)
    print("SHRINK RESP CHANNEL (VALID): ",shrink_resp_channel)
    print("ALLOC RESP CHANNEL (VALID): ",alloc_resp_channel)
    if(not(read_resp_channel0[2]==1 and read_resp_channel0[0]==2 and read_resp_channel0[1]==0xbeefdead)):
        print("TEST FAILED, Channel 0 unexpected")
        sys.exit()
    print("\n-----------------------------\n\n")

    #  Shrink the space
    read_channel0 = 0,0
    read_channel1 = 0,0
    update_channel0 = 0,0,0
    write_channel0 = 0,0,0
    write_channel1 = 0,0,0
    shrink_channel = 0,1
    alloc_channel = 0, 0,0, 0

    read_resp_channel0, read_resp_channel1, shrink_resp_channel, alloc_resp_channel = spad.run_cycle(read_channel0, update_channel0, write_channel0, read_channel1, write_channel1, alloc_channel, shrink_channel)
    print("Cycle 7")
    print("READ RESP CHANNEL0 (ID, DATA, VALID): ",read_resp_channel0)
    print("READ RESP CHANNEL1 (ID, DATA, VALID): ",read_resp_channel1)
    print("SHRINK RESP CHANNEL (VALID): ",shrink_resp_channel)
    print("ALLOC RESP CHANNEL (VALID): ",alloc_resp_channel)
    if(shrink_resp_channel != True):
        print("TEST FAILED, expected shrink response")
        sys.exit()
    print("\n-----------------------------\n\n")

    # Free the space
    read_channel0 = 0,0
    read_channel1 = 0,0
    update_channel0 = 0,0,0
    write_channel0 = 0,0,0
    write_channel1 = 0,0,0
    shrink_channel = 0,0
    alloc_channel = 0, 0, 1, 1

    read_resp_channel0, read_resp_channel1, shrink_resp_channel, alloc_resp_channel = spad.run_cycle(read_channel0, update_channel0, write_channel0, read_channel1, write_channel1, alloc_channel, shrink_channel)
    print("Cycle 8")
    print("READ RESP CHANNEL0 (ID, DATA, VALID): ",read_resp_channel0)
    print("READ RESP CHANNEL1 (ID, DATA, VALID): ",read_resp_channel1)
    print("SHRINK RESP CHANNEL (VALID): ",shrink_resp_channel)
    print("ALLOC RESP CHANNEL (VALID): ",alloc_resp_channel)
    if(alloc_resp_channel != True):
        print("TEST FAILED, expected alloc response")
        sys.exit()
    print("\n-----------------------------\n\n")

    print("\n\n\n TEST PASSED \n\n\n")
