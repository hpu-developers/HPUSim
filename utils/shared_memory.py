"""
  This module defines a class for shared memory hierarchy,
  to be used in cohesion with a L1 cache, scratchpad and
  TFU-private scratchpad to form the complete memory hierachy of HPU.
  For every load/store operation, it computes the cycles taken through the hierarchy,
  creating entries into a log file - shared_memory.log.

  At its core, it is a wrapper around a python based cache simulator - pycachesim.
  The original source code is in https://github.com/RRZE-HPC/pycachesim.git
  which we have modified to enable fine-grained logging and hence generate performance numbers.

	To build the dependency, clone abhiutd/pycachesim (https://github.com/abhiutd/pycachesim.git).
  Then run 'python setup.py build' followed by 'python setup.py install' to install it.

  System configuration

  L2 cache
  size: 256 kB
  associativity: 8-way
  replacement policy: LRU
  write properties: write back, write allocate, no write combining

  DRAM
  size: unlimited => hit on all requests

"""

import sys,re

from cachesim import CacheSimulator, Cache, MainMemory

class SharedMemory:

  def __init__(self):
    """
    Initialize shared memory subsystem

    Args:
      None

    Returns:
      None
    """
    # configuration
    self.log = "shared_memory.log"
    original_stdout = sys.stdout
    sys.stdout = open(self.log, "w+")
    print("======== SHARED MEMORY LOG ========")
    self.cacheline_size = 64

    # instantiate main memory
    self.main_mem = MainMemory()

    # instatiate L2 cache
    self.l2 = Cache(name="L2", sets=512, ways=8, cl_size=self.cacheline_size,replacement_policy="LRU", write_back=True, write_allocate=True, victims_to=None, swap_on_load=False)
    self.main_mem.load_to(self.l2)
    self.main_mem.store_from(self.l2)

    # add L2 latency numbers
    self.read_l2_from_mem = 80
    self.write_l2_to_mem = 100
    self.read_l2_hit = 14
    self.write_l2_hit = 14

    # instantiate shared memory subsystem
    self.cs = CacheSimulator(first_level=self.l2, main_memory=self.main_mem)

    sys.stdout.close()
    sys.stdout = original_stdout

    self.access_count = 0

  def read(self, addr, num_of_bytes=4):
    """
    This loads data starting at address addr

    Args:
      addr: base address
      num_of_bytes: number of bytes to load (assumed to be 4 for load_word)
    Returns:
      read_valid: boolean to depict if it was a valid read
      data: data to be returned (dummy data)
      addr: returning address for completeness sake
      cycles: memory access time across the hierarchy
    """
    # switch to local memory log file
    original_stdout = sys.stdout
    sys.stdout = open(self.log,"a")
    self.access_count += 1
    start_tag = "======== START LOAD-" + str(self.access_count) +" ========"
    print(start_tag)

    #### LOAD ####
    self.cs.load(addr, length=num_of_bytes)
    # define dummy data
    data = 0xdeadbeef
    # assume all reads to be valid
    read_valid = True

    #### POSTPROCESS TO COMPUTE NO OF CYCLES TAKEN ####

    # close local memory log file
    end_tag = "======== END LOAD-" + str(self.access_count) +" ========"
    print(end_tag)
    sys.stdout.close()
    sys.stdout = original_stdout

    # parse memory log file
    log_file = open(self.log, 'r')
    log_list = log_file.readlines()
    head = 0
    tail = 0
    count = 0
    for line in log_list:
      start_obj = re.search(start_tag, line, re.M|re.I)
      if start_obj:
        head = count
        count += 1
      else:
        end_obj = re.search(end_tag, line, re.M|re.I)
        if end_obj:
          tail = count
          count += 1
        else:
          count += 1

    cycles = 0
    for line_index in range(head+1,tail):
      line = log_list[line_index]
      line_fields = line.rstrip().split(" ")
      cache_level = line_fields[0]
      cache_action = line_fields[1]
      if cache_action == 'HIT':
        if cache_level == 'L2':
          cycles += self.read_l2_hit
        else:
          pass
      elif cache_action == "MISS":
        if cache_level == 'L2':
          cycles += self.read_l2_from_mem
        else:
          pass
      else:
        pass

    return read_valid, data, addr, cycles

  def write(self, data, addr, num_of_bytes=4):
    """
    This stores data starting at address addr

    Args:
      addr: base address
      num_of_bytes: number of bytes to store (assumed to be 4 for store_word)

    Returns:
      cycles: memory access time across the hierarchy
    """
    # switch to local memory log file
    original_stdout = sys.stdout
    sys.stdout = open(self.log,"a")
    self.access_count += 1
    start_tag = "======== START STORE-" + str(self.access_count) +" ========"
    print(start_tag)

    #### STORE ####
    self.cs.store(addr, length=num_of_bytes)

    #### POSTPROCESS TO COMPUTE NO OF CYCLES TAKEN ####

    # close local memory log file
    end_tag = "======== END STORE-" + str(self.access_count) +" ========"
    print(end_tag)
    sys.stdout.close()
    sys.stdout = original_stdout

    # parse memory log file
    log_file = open(self.log, 'r')
    log_list = log_file.readlines()
    head = 0
    tail = 0
    count = 0
    for line in log_list:
      start_obj = re.search(start_tag, line, re.M|re.I)
      if start_obj:
        head = count
        count += 1
      else:
        end_obj = re.search(end_tag, line, re.M|re.I)
        if end_obj:
          tail = count
          count += 1
        else:
          count += 1

    cycles = 0
    for line_index in range(head+1,tail):
      line = log_list[line_index]
      line_fields = line.rstrip().split(" ")
      cache_level = line_fields[0]
      cache_action = line_fields[1]
      if cache_action == 'HIT':
        if cache_level == 'L2':
          cycles += self.write_l2_hit
        else:
          pass
      elif cache_action == "MISS":
        if cache_level == 'L2':
          cycles += self.write_l2_to_mem
        else:
          pass
      else:
        pass

    return cycles

  def loadstore(self, addrs, num_of_bytes=4):
    """
    This loads and stores data starting at address addr

    Args:
      addrs: iterable of address tuples
      num_of_bytes: load and store between addr and addr+num_of_bytes

    Returns:
      None
    """
    self.cs.loadstore(addrs, length=num_of_bytes)

  def log_state(self):
    """
    Export parameters accumulated by backend simulator

    Args:
      None

    Returns:
      None
    """
    original_stdout = sys.stdout
    sys.stdout = open(self.log,"a")
    print("\n======== SHARED MEMORY STATS ========")
    print(self.cs.print_stats(file=sys.stdout))
    sys.stdout.close()
    sys.stdout = original_stdout

# Test Memory module
if __name__ == '__main__':

  shmem = SharedMemory()

  rvalid, data, addr, cycles = shmem.read(1234)
  assert cycles==80, "COLD START LOAD TEST FAILED!"
  #print("Number of cycles for loading at 1234: " + str(cycles))

  cycles = shmem.write(0xdeadbeef, 2232)
  assert cycles==100, "COLD START STORE TEST FAILED!"
  #print("Number of cycles for storing at 2232: " + str(cycles))

  rvalid, data, addr, cycles = shmem.read(1234)
  assert cycles==14, "CACHED LOAD TEST FAILED!"
  #print("Number of cycles for loading at 1234: " + str(cycles))

  shmem.log_state()
