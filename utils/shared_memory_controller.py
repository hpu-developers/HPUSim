"""
  This is a controller that instantiates a SharedMemory core and builds a wrapper
  around it to make it programmable. This is exposed to the programmer.

  The function calls accepted:
    load  <src> <dst>
    store <src> <dst>
 """
import Queue
import sys
from shared_memory import SharedMemory

class SharedMemoryController:

  def __init__(self):
    """
    Initialize controller with an instance of SharedMemory

    Args:
      None

    Returns:
      None
    """
    # configuration of L2 cache and DRAM are pre-defined in SharedMemory constructor
    self.bank = SharedMemory()
    self.read_queue_0 = Queue.Queue()
    self.read_queue_1 = Queue.Queue()
    self.write_queue_0 = Queue.Queue(maxsize=2)
    self.write_queue_1 = Queue.Queue(maxsize=2)
    # dictionary for cycle count for each active memory access
    self.cycles_left = dict()
    # FIX ME IN DEPENDENCY MANAGER LATER
    # create fields for each channel to allow reads and writes to the same address to happen simulatenously
    self.cycles_left['read_channel0'] = dict()
    self.cycles_left['write_channel0'] = dict()
    self.cycles_left['read_channel1'] = dict()
    self.cycles_left['write_channel1'] = dict()

    # dictionary for storing address for active memory access
    self.channel = dict()
    self.channel['read_channel0'] = 0
    self.channel['write_channel0'] = 0
    self.channel['read_channel1'] = 0
    self.channel['write_channel1'] = 0
    # store read response for each channel till cycle completion
    self.total_cycles = 0


  def run_cycle(self, read_channel0, write_channel0, read_channel1, write_channel1):
    """
    This is the main function to call the read/write request
    """
    # inputs
    araddr0, arvalid0 = read_channel0
    waddr0, wdata0, wvalid0 = write_channel0
    araddr1, arvalid1 = read_channel1
    waddr1, wdata1, wvalid1 = write_channel1

    # outputs
    rdata0 = 0
    rvalid0 = 0
    readID0 = None
    rdata1 = 0
    rvalid1 = 0
    readID1 = None
    read_cycles_channel0 = (None, 0, False)
    write_cycles_channel0 = (None, 0, False)
    read_cycles_channel1 = (None, 0, False)
    write_cycles_channel1 = (None, 0, False)

    ######### CHANNEL 0-1 #########

    #### WRITE ####
    # clear any previous completed accesses
    # check if a memory access is ongoing in the channel
    # if yes, decrement cycle count otherwise
    # pop write requests if any
    # debug
    #print("self.cycles_left: ", self.cycles_left)
    #print("self.channel['write_channel0']: ", self.channel['write_channel0'])
    if((self.channel['write_channel0'] != 0) and (self.cycles_left['write_channel0'][self.channel['write_channel0']] == 0)):
      # clear channel
      self.cycles_left['write_channel0'].pop(self.channel['write_channel0'])
      self.channel['write_channel0'] = 0

    if(self.channel['write_channel0'] != 0):
      self.cycles_left['write_channel0'][self.channel['write_channel0']] -= 1
    else:
      if(not self.write_queue_0.empty()):
        addr, data = self.write_queue_0.get()
        cycles_write_queue_0 = self.bank.write(data, addr)
        self.channel['write_channel0'] = addr
        # do not run one cycle of mem access now
        # this allows us to stay in sync with the corresponding store unit
        self.cycles_left['write_channel0'][addr] = cycles_write_queue_0
        # add cycles left to cycle channel of write_channel0 with valid signal
        write_cycles_channel0 = (addr, self.cycles_left['write_channel0'][addr], True)
        # debug
        print("Write Queue 0 -> addr: ", str(addr), ", data: ", str(data), ", write cycles : ", str(cycles_write_queue_0), "write_cycles_channel0: ", write_cycles_channel0)
      else:
        pass

    if((self.channel['write_channel1'] != 0) and (self.cycles_left['write_channel1'][self.channel['write_channel1']] == 0)):
      # clear channel
      self.cycles_left['write_channel1'].pop(self.channel['write_channel1'])
      self.channel['write_channel1'] = 0

    if(self.channel['write_channel1'] != 0):
      self.cycles_left['write_channel1'][self.channel['write_channel1']] -= 1
    else:
      if(not self.write_queue_1.empty()):
        addr, data = self.write_queue_1.get()
        cycles_write_queue_1 = self.bank.write(data, addr)
        self.channel['write_channel1'] = addr
        # do not run one cycle of mem access now
        # this allows us to stay in sync with the corresponding store unit
        self.cycles_left['write_channel1'][addr] = cycles_write_queue_1
        # add cycles left to cycle channel of write_channel1 with valid signal
        write_cycles_channel1 = (addr, self.cycles_left['write_channel1'][addr], True)
        # debug
        print("Write Queue 1 -> addr: ", str(addr), ", data: ", str(data), ", write cycles : ", str(cycles_write_queue_1), "write_cycles_channel1: ", write_cycles_channel1)
      else:
        pass

    # load write requests into the queue
    if(wvalid0):
      self.write_queue_0.put((waddr0, wdata0))
    if(wvalid1):
      self.write_queue_1.put((waddr1, wdata1))

    #### READ ####
    # no logic of outstanding reads in SharedMemory
    # clear any previous completed accesses
    # check if a memory access is ongoing in the channel
    # if yes, decrement cycle count otherwise
    # pop read requests if any
    valid_response_0 = False
    valid_response_1 = False
    if((self.channel['read_channel0'] != 0) and (self.cycles_left['read_channel0'][self.channel['read_channel0']] == 0)):
      # clear channel
      self.cycles_left['read_channel0'].pop(self.channel['read_channel0'])
      self.channel['read_channel0'] = 0

    if(self.channel['read_channel0'] != 0):
      self.cycles_left['read_channel0'][self.channel['read_channel0']] -= 1
      if(self.cycles_left['read_channel0'][self.channel['read_channel0']] == 0):
        # reperform load to update readID, rdata, rvalid values
        rvalid0, rdata0, readID0, cycles_read_queue_0 = self.bank.read(self.channel['read_channel0'])
        valid_response_0 = True
    else:
      if(not self.read_queue_0.empty()):
        addr, data = self.read_queue_0.get()
        rvalid0, rdata0, readID0, cycles_read_queue_0 = self.bank.read(addr)
        self.channel['read_channel0'] = addr
        # do not run one cycle of mem access now
        # this allows us to stay in sync with the corresponding load unit
        self.cycles_left['read_channel0'][addr] = cycles_read_queue_0
        # add cycles left to cycle channel of read_channel0 with valid signal
        read_cycles_channel0 = (addr, self.cycles_left['read_channel0'][addr], True)
        # debug
        print("Read Queue 0 -> addr: ", str(addr), ", read cycles to wait : ", str(cycles_read_queue_0), "read_cycles_channel0: ", read_cycles_channel0)
      else:
        pass

    if((self.channel['read_channel1'] != 0) and (self.cycles_left['read_channel1'][self.channel['read_channel1']] == 0)):
      # clear channel
      self.cycles_left['read_channel1'].pop(self.channel['read_channel1'])
      self.channel['read_channel1'] = 0

    if(self.channel['read_channel1'] != 0):
      self.cycles_left['read_channel1'][self.channel['read_channel1']] -= 1
      if(self.cycles_left['read_channel1'][self.channel['read_channel1']] == 0):
        # reperform load to update readID, rdata, rvalid values
        rvalid1, rdata1, readID1, cycles_read_queue_1 = self.bank.read(self.channel['read_channel1'])
        valid_response_1 = True
    else:
      if(not self.read_queue_1.empty()):
        addr, data = self.read_queue_1.get()
        rvalid1, rdata1, readID1, cycles_read_queue_1 = self.bank.read(addr)
        self.channel['read_channel1'] = addr
        # do not run one cycle of mem access now
        # this allows us to stay in sync with the corresponding load unit
        self.cycles_left['read_channel1'][addr] = cycles_read_queue_1
        # add cycles left to cycle channel of read_channel1 with valid signal
        read_cycles_channel1 = (addr, self.cycles_left['read_channel1'][addr], True)
        # debug
        print("Read Queue 1 -> addr: ", str(addr), ", read cycles : ", str(cycles_read_queue_1), "read_cycles_channel1: ", read_cycles_channel1)

    # push requests to the queue
    if(arvalid0):
      self.read_queue_0.put((araddr0, 0))
    if(arvalid1):
      self.read_queue_1.put((araddr1, 1))

    #### RESPONSE ####
    # combine results and respond
    # return load value only when cycles complete
    if(not valid_response_0):
      rvalid0 = 0
    if(not valid_response_1):
      rvalid1 = 0
    read_resp_channel0 = readID0, rdata0, rvalid0
    read_resp_channel1 = readID1, rdata1, rvalid1

    # combine all read/write_cycles_channels into one single tuple for ease of management
    # (r0,w0,r1,w1)
    cycles_resp_channel = (read_cycles_channel0, write_cycles_channel0, read_cycles_channel1, write_cycles_channel1)

    # increment total cycle count
    self.total_cycles += 1

    # debug
    #print("==== System status ====")
    #print("Total cycles: ", self.total_cycles)
    #print("Read Queue 0 : ", list(self.read_queue_0.queue))
    #print("Read Queue 1 : ", list(self.read_queue_1.queue))
    #print("Write Queue 0 : ", list(self.write_queue_0.queue))
    #print("Write Queue 1 : ", list(self.write_queue_1.queue))
    #print("Read Channel 0 : ", self.channel['read_channel0'])
    #print("Read Channel 1 : ", self.channel['read_channel1'])
    #print("Write Channel 0 : ", self.channel['write_channel0'])
    #print("Write Channel 1 : ", self.channel['write_channel1'])

    #for i in self.cycles_left.keys():
    #  print("addr: ", i," => ", self.cycles_left[i])

    return read_resp_channel0, read_resp_channel1, cycles_resp_channel

if __name__ == "__main__":

  # instantiate a shared memory controller
  shmem_controller = SharedMemoryController()

  # initialize channels to something
  read_channel0 = 0,0
  read_channel1 = 0,0
  write_channel0 = 0,0,0
  write_channel1 = 0,0,0

  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)
  print("CYCLE 0")
  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  print("\n-----------------------------\n\n")

  read_channel0 = 0,0
  read_channel1 = 0,0
  write_channel0 = 1234,10,1
  write_channel1 = 0,0,0

  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)
  print("CYCLE 1")
  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  print("\n-----------------------------\n\n")

  read_channel0 = 2232,1
  read_channel1 = 0,0
  write_channel0 = 0,0,0
  write_channel1 = 0,0,0

  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)
  print("CYCLE 2")
  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  print("\n-----------------------------\n\n")

  read_channel0 = 0,0
  read_channel1 = 0,0
  write_channel0 = 0,0,0
  write_channel1 = 1336,12,1
  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0,write_channel0, read_channel1, write_channel1)
  print("CYCLE 3")
  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  print("\n-----------------------------\n\n")

  read_channel0 = 0,0
  read_channel1 = 1500,1
  write_channel0 = 1260,11,1
  write_channel1 = 0,0,0

  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)
  print("CYCLE 4")
  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  print("\n-----------------------------\n\n")

  # modify range of iterator to see different accesses getting to completion
  for i in range(0,85):
    read_channel0 = 0,0
    read_channel1 = 0,0
    write_channel0 = 0,0,0
    write_channel1 = 0,0,0

    read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)
    print("CYCLE ", shmem_controller.total_cycles)
    print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
    print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
    print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
    print("\n-----------------------------\n\n")
