"""
    Implements a highly programmable scratchpad.

    Supports a design maximum number of regions (when implemented in hardware).

    Supported functions:

        1. Read
        2. Write
        3. Allocate
        4. readReady
        5. shrink
        6. checkReadyReads
        7. clearReadyRead
        8. checkOutstandingReads
        9. moveOutstandingReads


"""

class buffet:

    def __init__(self, size):

        self.size               = size
        self.regfile            = [0]*size
        self.valid_read_ranges  = []
        self.valid_ranges       = []
        self.outstanding_queue  = []
        self.ready_queue        = []

    def read(self, addr, readID=0):
        """
            Read the requested data, if there is a pending update,
            then queue the response.
        """
        read_valid, data_valid = self.addrInReadRange(addr)
        # If already in valid range, then we give back the data and addr (as the ID)
        if(read_valid):
            return 1, self.regfile[addr], addr, readID
        # If not, then we queue this as an outstanding read
        elif(data_valid):
            self.outstanding_queue.append((addr, readID))
            return 0, None, None, None
        # Else this is not a valid read
        else:
            return 0, None, None, None

    def allocate(self, base, size):
        """
            Allocates a space and adds a valid range, head & tail.
        """
        # Current implementation: It is user's responsibility to make sure there are no
        # overlaps in the regions (we won't check)
        self.valid_ranges.append([base, (base + size)%self.size])
        self.valid_read_ranges.append([base, base])

        return True

    def free(self, base):
        """
            Removes the allocation.
        """
        # Find out if the requested base is present.
        valid, ID = self.baseInRange(base)

        if(valid):
            del(self.valid_ranges[ID])
            del(self.valid_read_ranges[ID])
            return True
        else:
            return False

    def readReady(self):
        """
            Return if the spad is ready for accepting reads
        """
        return ((not self.outstanding_queue.full()) and self.valid_read_ranges)

    def update(self, addr, data):
        """
            Update a specific address (should be within the readrange)
        """
        # check if the requested base address is present
        valid, ID = self.addrInReadRange(addr)

        # Update the requested address
        if(valid):
            self.regfile[addr] = data
            return True
        else:
            return False

    def write(self, base, data):
        """
            Writes to the tail and increments the tail.
        """
        # We do not perform any checks other than checking if it is in one of the valid
        # ranges. Also, the tail can not go beyond the range.

        # check if the requested base address is present
        valid, ID = self.baseInRange(base)


        if(valid):
            # Make sure tail has not already hit the bound
            tail = self.valid_read_ranges[ID][1]
            bound = self.valid_ranges[ID][1]
            if(tail>=bound):
                return False
            else:
                next_tail = min(bound, tail+1)
                self.regfile[tail] = data
                self.valid_read_ranges[ID][1] = next_tail
                return True
        else:
            return False

    def shrink(self, base):
        """
            Shrinks the allocated space (erases everything by moving head, tail)
        """
        # We check two things, whether the requested head is currently present, and if the
        # requested shrink size is valid.
        valid, ID = self.baseInRange(base)

        if(valid):
            self.valid_read_ranges[ID] = [base, base]
            return 1
        else:
            return 0

    def checkOutstandingReads(self):
        """
            Return true if there are any outstanding reads,
        """
        return (len(self.outstanding_queue) >0)

    def moveOutstandingReads(self):
        """
            We check the outstanding read queue to see if any of them are ready to be read.
            If yes, then that should be given the priority, hence transferred to the ready queue.
        """

        # Do all this only if there is some outstanding read.
        if(self.outstanding_queue):
            outstanding_queue_new = []
            for outstandingRead,readID in self.outstanding_queue:
                if(self.addrInReadRange(outstandingRead)):
                    self.ready_queue.append((outstandingRead,readID))
                else:
                    outstanding_queue_new.append((outstandingRead, readID))

            self.outstanding_queue = outstanding_queue_new

        return None

    def checkReadyReads(self):
        """
            This returns true if there are any outstanding reads that are now ready.
        """

        return (len(self.ready_queue) >0)

    def clearReadyRead(self):
        """
            This function clears the outstanding read that is now ready to be read.
            This should get the priority over a new read request.
        """
        addr, readID = self.ready_queue[0]
        data = self.regfile[addr]
        # clear the entry
        del(self.ready_queue[0])

        return 1, data, addr, readID

    def addrInReadRange(self, addr):
        """
            Returns True if the requested address is in the valid window.

            Output: (Whether data is ready to read, Whether data is even in Range)
        """
        valid, idx = self.addrInRange(addr)
        if(valid):
            head, tail = self.valid_read_ranges[idx]
            read_valid = (addr >= head) and (addr < tail)
            if(head < tail):
                    return read_valid, True
            else:
                    return not read_valid, True
        else:
            return False, False

    def addrInRange(self, addr):
        """
            This is a helper function that reads through the valid ranges and returns the ID.
        """
        # Check which allocation it belongs to
        for idx, (base,bound) in enumerate(self.valid_ranges):
            if(addr in range(base, bound)):
                return True, idx

        return False, None

    def baseInRange(self, addr):
        """
            This is a helper function that reads through the valid ranges and returns the ID.
        """
        # Check which allocation it belongs to
        for idx, (base,bound) in enumerate(self.valid_ranges):
            if(addr == base):
                return True, idx

        return False, None

    def getOccupancy(self):
        """
            Returns the total occupancy of the scratchpad
        """
        occupancy = 0
        for head,tail in self.valid_read_ranges:
            occupancy += (tail-head) if (head<=tail) else (self.size -head + tail)

        return occupancy

if __name__ == "__main__":
    """
        Test a sequence of things.
    """
    import sys

    # Instantiate the scratchpad
    spad = buffet(128)
    # Allocate region A
    spad.allocate(0,16)
    # Write something to address 0 of that region
    spad.write(0, 0xdeadbeef)
    # Read the same data
    _, val, _,_ = spad.read(0)
    # Test if the correct value was returned
    if(val != 0xdeadbeef):
        print("TEST FAILED, STAGE 1")
        sys.exit()
    # Test for any outstanding reads
    assert spad.checkOutstandingReads()==False, "TEST FAILED, STAGE 2"
    # Request for a read for which the data does not exist yet
    spad.read(1)
    # Now there should be an outstanding read
    assert spad.checkOutstandingReads()==True, "TEST FAILED, STAGE 3"
    # Write a value and check outstanding reads
    spad.write(0, 0xdeadbeef)
    # Perform moving of outstanding to ready
    spad.moveOutstandingReads()
    # We should see a ready read on the ready_queue
    assert spad.checkReadyReads()==True, "TEST FAILED, STAGE 4"
    # Let's read the outstanding read
    _, val, addr,_ = spad.clearReadyRead()
    if((val != 0xdeadbeef) or (addr != 1)):
        print("TEST FAILED, STAGE 5")
        sys.exit()
    # Test the occupancy
    assert spad.getOccupancy()==2, "TEST FAILED, STAGE 6"
    # Now shrink the head
    spad.shrink(0)
    # Occupancy should reduce
    assert spad.getOccupancy()==0, "TEST FAILED, STAGE 6"
    # THis should entirely delete the allocation
    spad.free(0)
    # Confirm that no entries exist
    assert len(spad.valid_ranges)==0, "TEST FAILED, STAGE 7"

    print("TEST PASSED!")


