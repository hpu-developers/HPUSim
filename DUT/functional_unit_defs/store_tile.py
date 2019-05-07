"""
  This module implements store_tile unit for HPU
  It is supposed to fetch data from L2 + DRAM and
  write it to scratchpad
"""
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))+'/utils')

from random import randint
from functional_unit import FunctionalUnit
from accelerators import iCPU, iTFU

class StoreTile(FunctionalUnit):
  """
  class for simulating a load_tile unit for HPU instructions.
  """
  def __init__(self, name, ID):
    """
    Initialize attributes

      Args:
        ID: A string which should be present in accelerators.py

      Return:
        None
    """
    self.waiting_for_cycles = 0
    self.addr = 0
    FunctionalUnit.__init__(self, name, ID)

  def run_new_task_if_given(self, task):
    """
    This initiates execution of new load_unit in the functional unit and runs a cycle
    for it. We assume no cycles are required for task setup.

    Args:
      task: task dictionary or null

    Return:
      addr: address of requested load
    """
    if((task is not None) and (task['accelerator'] == self.name)):
      # setup task execution
      if(self.tfu_or_cpu == 'cpu'):
        ## debug
        print("Performing store_tile operation in memory unit!")
        self.task_counter = 0
        self.waiting_for_cycles = 1
        print("In run_new_task -> ", task['data']['out'])
        self.addr = task['data']['out'][0]
        self.task = task
        # write output to task for CDB to pick up later
        task['result'] = self.result
        self.result_dst = task['data']['out'][0]
        task['dest'] = self.addr
      else:
        sys.exit("Trying to run something different than an integer add on an integer adder!")
    else:
      self.busy = 0

    return self.addr

  def run_cycle(self, task, ack, abort, AccStatus, cache_controller_resp):
    """
    This runs a cycle for the functional unit.
    Each cycle can have a task coming in, have an
    existing task running or no task running.

      Args:
        task: (task dictionary or null, valid)
        ack: (accelerator, task_id, valid) (CDB)
        abort: (task_id, Valid)signal to kill existing running task
        cache_controller_resp: (addr, cycles, valid) response from cache_controller for current load
      Return:
        (task, task_valid, addr, addr_valid) if the task is done and/or need to contact memory
     """
    # increment cycle_counter
    self.cycle_counter += 1

    # Both abort and task valid cannot be high at the same time
    assert (not(abort[1] and task[1] and self.busy)), "I can not handle task_start and task_kill at  the same time....I is %s"% (self.name)

    # If abort signal comes and this FU is currently running something
    if abort[1] and self.busy:
      # if the task_id matches
      if (self.task['task_id'] == abort[0]):
        # Now change the ASR and make the FU idle
        # ASR can be modified from here IF AND ONLY IF abort comes
        if(self.tfu_or_cpu == 'cpu'):
          AccStatus.status_reg[iCPU[self.task['accelerator']]['ID'][0]] = 0
        self.ack_task_end()
    else:
      # do nothing..this task was not meant for this FU
      pass

    # Take action based on the acknowledgement
    # ack should be for this accelerator for the task it requested
    if(ack[5] == 1):
      ## debug
      #print("Received ack: ", ack, "ack[1]: ", ack[1], " == ", self.ID)
      if(ack[1] == self.ID):
        ## debug
        #print("Received ack ID matched: ", ack[1])
        if((ack[2] == self.task['task_id']) and (self.busy == 1) and (self.request_end == 1)):
          if(self.tfu_or_cpu == 'cpu'):
            AccStatus.status_reg[iCPU[self.task['accelerator']]['ID'][0]] = 0
          else:
            pass
          ## debug
          #print("Trying to call ack_task_end to!")
          self.ack_task_end()

    # Start a job if a valid task is given
    # ASSUMPTION : Task will not be given if the accelerator is Busy
    # Case 1: new valid task is given
    # Case 2: waiting for cycles expended in the load op
    # Case 3: busy while running through cycles
    if(task[1]):
      ## debug
      #print("Trying to call run_new_task_if_given -> ")
      #print("request_end: ", self.request_end, ", busy: ", self.busy, ", waiting_for_cycles: ", self.waiting_for_cycles)
      assert ((self.request_end == 0) and (self.busy == 0) and (self.waiting_for_cycles == 0)), "No task can come while I am busy... I  is %s"% (self.name)
      self.request_end = 0
      print("task ->", task[0])
      print("task data: ", task[0]['data'], " , ", "task src1: ", task[0]['src1'])
      task[0]['src0_end'] = task[0]['data']['out'][0] + task[0]['src1']
      req_addr = self.run_new_task_if_given(task[0])
      return ((None,0, req_addr, 1), AccStatus)
    elif(self.waiting_for_cycles == 1):
      # debug
      # print("In waiting_for_cycles!")
      # even though we have initalized the FU with a task
      # it is still spinning on its request for cycles from cache_controller
      if(cache_controller_resp[2]):
        if(self.addr == cache_controller_resp[0]):
          self.task_counter = cache_controller_resp[1]
          self.waiting_for_cycles = 0
          self.busy = 1
          # run task for the first time
          cycles_left = self.run_existing_task()
          # take care of one cycle accesses as well although
          # that we should face the case of 1-cycle access ever
          # even for spad
          if((cycles_left == 0) and (self.request_end == 0)):
            # start handshake for resetting execution
            self.request_end =  1
            #Since this is a dummy execution, add a random result field
            self.task['result'] = randint(1,5)
            return ((self.task, 1, self.addr, 0), AccStatus)
          else:
            return ((None, 0, None, 0), AccStatus)
        else:
          sys.exit("Received cycles for incorrect lw instruction!")
      else:
        print("Still waiting for cycles requested!")
        return ((None, 0, None, 0), AccStatus)
    elif(self.busy == 1):
      # check if running a task
      cycles_left = self.run_existing_task() # running
      if((cycles_left == 0) and (self.request_end == 0)):
        # check if addr in tile left
        if(self.task['data']['out'][0] + 4 < self.task['src0_end']):
          print("Condition check: ", self.task['data']['out'][0] + 4, " < ", self.task['src0_end'] )
          self.task['data']['out'][0] += 4
          req_addr = self.run_new_task_if_given(self.task)
          return ((None,0, req_addr, 1), AccStatus)
        else:
          # start handshake for resetting execution
          self.request_end =  1
          #Since this is a dummy execution, add a random result field
          self.task['result'] = randint(1,5)
          return ((self.task, 1, self.addr, 0), AccStatus)
      else:
        return ((None, 0, None, 0), AccStatus)
    else:
      return ((None, 0, None, 0), AccStatus)

  def ack_task_end(self):
    """
    This resets execution on FU only if acknowledgement == 1

    Args:
      None

    Return:
      reset: 1 if reset done
    """
    ## debug
    print("Inside ack_task_end to!")

    ## object specific resetting
    self.waiting_for_cycles = 0
    self.addr = 0

    # reset execution
    self.task_counter = 0
    self.task = None
    self.busy = 0
    self.request_end = 0
    self.result = 0
    self.result_dst = 0

    return 1

if __name__ == "__main__":

  from acc_status import AccStatus
  from accelerators import *
  from shared_memory_controller import SharedMemoryController

  #### CREATE A CPU STORE TILE TASK ####
  # store_tile 100, 8, 124
  task1 = { 'accelerator' : 'store_tile',
            'src0'        : 'R2',
            'src1'        : 8,
            'dst'         : 10,
            'control'     : 0,
            'task_id'     : 4,
            'data'        : {'in': [10, False], 'out': [10]}
          }

  # store_tile 100, 16, R3
  task2 = { 'accelerator' : 'store_tile',
             'src0'        : 'R3',
             'src1'        : 16,
             'dst'        : 200,
             'control'     : 0,
             'task_id'     : 5,
             'data'        : {'in': [100, False], 'out': [200]}
           }

  #### CREATE STORE_TILE UNIT AND MEMORY SUBSYSTEM (L2 + DRAM) ####
  lw = StoreTile('store_tile', 37)
  CDB = (None, None, None, None, None, 0)
  status = AccStatus(total_accelerators_count)
  # instantiate a shared memory controller
  shmem_controller = SharedMemoryController()

  #### RUN CYCLE 0 ####
  print("\n\n======== CYCLE 0 ========\n\n")
  # load unit
  req = lw.run_cycle((None, False), CDB, (None, False), status, (None, 0, False))
  print("Returned request -- ", req)
  # memory subsystem
  # initialize channels to something
  read_channel0 = 0,0
  read_channel1 = 0,0
  write_channel0 = 0,0,0
  write_channel1 = 0,0,0
  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)

  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  # log load unit execution
  # refer to cpu_memory.log for log of memory subsystem execution
  lw.log_state()

  #### RUN CYCLE 1 ####
  print("\n\n======== CYCLE 1 ========\n\n")
  print("======Starting load execution======")
  # Run task 1
  req = lw.run_cycle((task1, True), CDB, (None, False), status, (None, 0, False))
  print("Returned request -- ", req)
  # memory subsystem
  # connect load unit to read_channel0 of the controller
  # NOTE: cycles_resp_channel goes into load unit in the next cycle
  read_channel0 = 0,0
  read_channel1 = 0,0
  write_channel0 = req[0][2], 12, req[0][3]
  write_channel1 = 0,0,0
  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)

  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  # log load unit execution
  # refer to cpu_memory.log for log of memory subsystem execution
  lw.log_state()

  #### RUN CYCLE 2 ####
  print("\n\n======== CYCLE 2 ========\n\n")
  req = lw.run_cycle((task1, False), CDB, (None, False), status, cycles_resp_channel[1])
  print("Returned request -- ", req)
  # memory subsystem
  # connect load unit to read_channel0 of the controller
  # NOTE: cycles_resp_channel goes into load unit in the next cycle
  read_channel0 = 0, 0
  read_channel1 = 0,0
  write_channel0 = req[0][2], 12, req[0][3]
  write_channel1 = 0,0,0
  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)

  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  # log load unit execution
  # refer to cpu_memory.log for log of memory subsystem execution
  lw.log_state()

  #### RUN CYCLE 3 ####
  ## Replacing task1 with task2 gives out an error suggesting that since the load unit is already running
  ## a task, it cannot entertain another one
  ## it is the responsibility of res_station to ensure that it pushes a task only when the load unit is idle
  print("\n\n======== CYCLE 3 ========\n\n")
  req = lw.run_cycle((task2, False), CDB, (None, False),status, cycles_resp_channel[1])
  print("Returned request -- ", req)
  # memory subsystem
  # connect load unit to read_channel0 of the controller
  # NOTE: cycles_resp_channel goes into load unit in the next cycle
  read_channel0 = 0,0
  read_channel1 = 0,0
  write_channel0 = req[0][2], 12, req[0][3]
  write_channel1 = 0,0,0
  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)

  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  # log load unit execution
  # refer to cpu_memory.log for log of memory subsystem execution
  lw.log_state()

  #### RUN CYCLE 4 ####
  print("\n\n======== CYCLE 4 ========\n\n")
  req = lw.run_cycle((task1, False), CDB, (None, False), status, cycles_resp_channel[1])
  print("Returned request -- ", req)
  # memory subsystem
  # connect load unit to read_channel0 of the controller
  # NOTE: cycles_resp_channel goes into load unit in the next cycle
  read_channel0 = 0,0
  read_channel1 = 0,0
  write_channel0 = req[0][2], 12, req[0][3]
  write_channel1 = 0,0,0
  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)

  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  # log load unit execution
  # refer to cpu_memory.log for log of memory subsystem execution
  lw.log_state()

  # Run task 1 to completion
  for i in range(5, 110):
    #### RUN CYCLE i ####
    stmt = "\n\n======== CYCLE "+str(i)+" ========\n\n"
    print(stmt)
    req = lw.run_cycle((task1, False), CDB, (None, False), status, cycles_resp_channel[1])
    print("Returned request -- ", req)
    # memory subsystem
    # connect load unit to read_channel0 of the controller
    # NOTE: cycles_resp_channel goes into load unit in the next cycle
    read_channel0 = 0,0
    read_channel1 = 0,0
    write_channel0 = req[0][2], 12, req[0][3]
    write_channel1 = 0,0,0
    read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)

    print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
    print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
    print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
    # log load unit execution
    # refer to cpu_memory.log for log of memory subsystem execution
    lw.log_state()

  # wrap up task on load unit
  #### RUN CYCLE 102 ####
  print("\n\n======== CYCLE 102 ========\n\n")
  CDB = ('store_tile', 37, 4, 12, None, True)
  req = lw.run_cycle((None, False), CDB, (None, False), status, cycles_resp_channel[1])
  print("Returned request -- ", req)
  # memory subsystem
  # connect load unit to read_channel0 of the controller
  # NOTE: cycles_resp_channel goes into load unit in the next cycle
  read_channel0 = 0,0
  read_channel1 = 0,0
  write_channel0 = req[0][2], 12, req[0][3]
  write_channel1 = 0,0,0
  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)

  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  # log load unit execution
  # refer to cpu_memory.log for log of memory subsystem execution
  lw.log_state()

  #### RUN CYCLE 103 ####
  print("\n\n======== CYCLE 103 ========\n\n")
  CDB = (None, None, None, None, None, 0)
  req = lw.run_cycle((None, False), CDB, (None, False), status, cycles_resp_channel[1])
  print("Returned request -- ", req)
  # memory subsystem
  # connect load unit to read_channel0 of the controller
  # NOTE: cycles_resp_channel goes into load unit in the next cycle
  read_channel0 = 0,0
  read_channel1 = 0,0
  write_channel0 = req[0][2], 12, req[0][3]
  write_channel1 = 0,0,0
  read_resp_channel0, read_resp_channel1, cycles_resp_channel = shmem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)

  print("READ RESP CHANNEL0 (ID, DATA, VALID): ", read_resp_channel0)
  print("READ RESP CHANNEL1 (ID, DATA, VALID): ", read_resp_channel1)
  print("CYCLES RESP CHANNEL (ID, CYCLES, VALID) X 4: ", cycles_resp_channel)
  # log load unit execution
  # refer to cpu_memory.log for log of memory subsystem execution
  lw.log_state()
