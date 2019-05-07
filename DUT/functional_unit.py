"""
  This module defines a class for a generic functional unit in HPU.
  It could be configured to execute either CPU instructions or TFU tasks.
  As far as implementation is concerned, it is supposed to be inherited to
  create new <X>FunctionalUnit modules (X=add/mul/fft_256 etc). This would require
  the implementer to override run_new_task_if_given() method to perform actual
  computation/memory access, figure out number of cycles it takes and assign that
  to self.task_counter attribute, which would be decremented in run_existing_task()
  consequently till it is complete.
"""

import sys
from random import randint

from accelerators import iCPU, iTFU

class FunctionalUnit:
  """
  class for simulating a functional unit

  An instance of this class is meant to be placed after
  the unit's reservation stations. It contains a counter
  to mimic execution of its current task. Note that we assume
  a master-slave setup, where each FunctionalUnit is a slave
  who does what it is told to do. Its associated ReservationStation
  is responsible for scheduling a task on it.
  Attributes:
    ID: A string which depicts its functionality
    cycle_counter: A counter to keep track of synchronizing clock
    task_counter: A counter to mimic task execution
    task: A variable which stores currently running task if any
    busy: A boolean to signify busyness/idleness
    valid: A boolean to signify validity of a cycle run
  """

  def __init__(self, name, ID):
    """
    Initialize attributes

      Args:
        ID: A string which should be present in accelerators.py

      Returns:
        None
    """
    self.name = name
    self.ID   = ID
    self.cycle_counter = 0
    self.task_counter = 0
    self.task = None
    self.busy = 0
    self.request_end = 0
    self.result = 0
    self.result_dst = 0
    if(name in iCPU.keys()):
      self.tfu_or_cpu = 'cpu'
    elif(name in iTFU.keys()):
      self.tfu_or_cpu = 'tfu'
    else:
      # Undefined functionality
      sys.exit("Trying to create an accelerator with undefined functionality!")

    return None

  def run_cycle(self, task, ack, abort, AccStatus):
    """
    This runs a cycle for the functional unit.
    Each cycle can have a task coming in, have an
    existing task running or no task running.

    Args:
      task: (task dictionary or null, valid)
      ack: (accelerator, task_id, valid) (CDB)
      abort: (task_id, Valid)signal to kill existing running task

    Return:
      (task, valid) only if the task is done
    """
    # increment cycle_counter
    self.cycle_counter += 1

    # Both abort and task valid cannot be high at the same time
    assert (not(abort[1] and task[1] and self.busy)), "I can not handle task_start and task_kill at the same time....I is %s"% (self.name)

    # If abort signal comes and this FU is currently running something
    if abort[1] and self.busy:
      # if the task_id matches
      if (self.task['task_id'] == abort[0]):
        # Now change the ASR and make the FU idle
        # ASR can be modified from here IF AND ONLY IF abort comes
        #### TODO loop over 'ID' list for multiple instances
        if(self.tfu_or_cpu == 'cpu'):
          AccStatus.status_reg[iCPU[self.task['accelerator']]['ID'][0]] = 0
        else:
          AccStatus.status_reg[iTFU[self.task['accelerator']]['ID'][0]] = 0
        self.ack_task_end()
    else:
      # do nothing..this task was not meant for this FU
      pass
      #assert False, "Bro...I got a task to kill which I ain't running...I is %s"% (self.name)

    # Take action based on the acknowledgement
    # ack should be for this accelerator for the task it requested
    if(ack[5] == 1):
      if(ack[1] == self.ID):
        if((ack[2] == self.task['task_id']) and (self.busy == 1) and (self.request_end == 1)):
          # need to set the status register to 0
          #### TODO loop over 'ID' list for multiple instances
          if(self.tfu_or_cpu == 'cpu'):
            AccStatus.status_reg[iCPU[self.task['accelerator']]['ID'][0]] = 0
          elif(self.tfu_or_cpu == 'tfu'):
            AccStatus.status_reg[iTFU[self.task['accelerator']]['ID'][0]] = 0
          self.ack_task_end()

    # Start a job if a valid task is given
    # ASSUMPTION : Task will not be given if the accelerator is Busy
    if(task[1]):
      assert ((self.request_end == 0) and (self.busy == 0)), "No task can come while I am busy... I is %s"% (self.name)
      self.request_end = 0
      self.run_new_task_if_given(task[0]) # not running
      return ((None,0), AccStatus)
    elif(self.busy == 1):
      # check if running a task
      cycles_left = self.run_existing_task() # running
      if((cycles_left == 0) and (self.request_end == 0)):
        # start handshake for resetting execution
        self.request_end =  1
        #Since this is a dummy execution, add a random result field
        #self.task['result'] = randint(1,5)
        return ((self.task, 1), AccStatus)
      else:
        return ((None, 0), AccStatus)
    else:
      return ((None, 0), AccStatus)

  def run_new_task_if_given(self, task):
    """
    This initiates execution of a new task on the functional unit and runs a cycle
    for it. We assume no cycles are required for task setup.

    Args:
      task: task dictionary or null

    Return:
      None
    """
    if((task is not None) and (task['accelerator'] == self.name)):
      # setup task execution
      if(self.tfu_or_cpu == 'cpu'):
        self.task_counter = iCPU[self.name]['cycles'] - 1
        # perform dummy computation
        if((task['data']['in'][0] is not None) and (task['data']['in'][0] is not None)):
          self.result = task['data']['in'][0] + task['data']['in'][1]
        task['result'] = self.result
        task['dest'] = task['data']['out'][0]
        self.result_dst = task['data']['out'][0]
        task['dest'] = self.result_dst
        self.busy = 1
        self.task = task
      elif(self.tfu_or_cpu == 'tfu'):
        self.task_counter = iTFU[self.name]['cycles'] - 1
        self.result = task['data']['out'][0]
        task['result'] = self.result
        self.result_dst = task['data']['out'][0]
        task['dest'] = self.result_dst
        self.busy = 1
        self.task = task
      else:
        pass
    else:
      self.busy = 0

    return None

  def run_existing_task(self):
    """
    This runs a cycle for an existing task on the functional unit.

    Args:
      None

    Return:
      task_counter: cycles left
    """
    if((self.task is not None) and (self.task_counter > 0)):
      self.task_counter -= 1
      self.busy = 1
      return self.task_counter
    elif((self.task is not None) and (self.task_counter == 0)):
      return 0
    else:
      # Task run failed
      sys.exit("Trying to run a task not present on the accelerator!")

    return None

  def abort_task(self):
    """
    Aborts current running task if speculation went wrong
    """
    self.busy = 0
    self.task_counter = 0
    self.task = None

    return None

  def ack_task_end(self):
    """
    This resets execution on FU only if acknowledgement == 1

    Args:
      None

    Return:
      reset: 1 if reset done
    """
    # reset execution
    self.task_counter = 0
    self.task = None
    self.busy = 0
    self.request_end = 0
    self.result = 0
    self.result_dst = 0

    return 1

  def query_task(self):
    """
    Returns the current task on the FU
    """
    return self.task

  def check_state(self):
    """
    Returns 1 if busy, returns 0 if free
    """
    return self.busy

  def log_state(self):
    """
    Export state of the functional unit

    Args:
      None

    Returns:
      None
    """
    print("Functional Unit : ", str(self.name) + '_' + str(self.ID))
    print("Running for : ", self.cycle_counter, "cycles")
    print("Busy : ", self.busy)
    print("Task : ", self.task)
    print("Task cycles left : ", self.task_counter)
    print("\n")

#TODO : Update this based on changes for acknowledgement

if __name__ == "__main__":

  from acc_status import AccStatus
  from accelerators import *

  # Create a task
  task1 = { 'accelerator' : "fft_256",
            'inp0_mem'    : 0,
            'inp0_size'   : 1800,
            'inp1_mem'    : 1810,
            'inp1_size'   : 1800,
            'out_mem'     : 4000,
            'out_size'    : 1000,
            'task_id'     : 0,
            'pid'         : 0,
            'control'     : 0,
            'data'        : {'in': [1,2], 'out': [3]}
          }

  task2 = { 'accelerator' : "add",
            'src0'        : 0,
            'src1'        : 1900,
            'dst'         : 2200,
            'control'     : 0,
            'data'        : {'in': [1,2], 'out': [3]}
          }

  task3 = { 'accelerator' : "xyzw",
            'inp_mem'     : 0,
            'inp_size'    : 1800,
            'out_mem'     : 2000,
            'out_size'    : 1000,
            'task_id'     : 3,
            'pid'         : 0,
            'data'        : {'in': [1,2], 'out': [3]}
          }

  # Create its corresponding functional unit
  tfu1 = FunctionalUnit('fft_256', 7)
  cpu1 = FunctionalUnit('add', 15)
  CDB = (None, None, None, None, None, False)
  status = AccStatus(total_accelerators_count)

  # Run no task on it
  tfu1.run_cycle((None, False), CDB, (None, False), status)
  tfu1.log_state()
  cpu1.run_cycle((None, False), CDB, (None, False), status)
  cpu1.log_state()

  print("======Starting fft_256 execution======")
  # Run task 1
  tfu1.run_cycle((task1, True), CDB, (None, False), status)
  tfu1.log_state()
  # Run task 1 to completion
  job_end = 0
  for i in range(0, iTFU['fft_256']['cycles']-1):
    job_end = tfu1.run_cycle((None, False), CDB, (None, False), status)
    print("job_end : ", job_end)
    tfu1.log_state()
  # ack task end
  # job_end should be 1 now
  tfu1.ack_task_end()
  print("\nShould have made FU idle!")
  tfu1.log_state()
  print("======Ending fft_256 execution======")


  print("======Starting add execution======")
  # Run task 2
  cpu1.run_cycle((task2, True), CDB, (None, False), status)
  cpu1.log_state()
  # Run task 2 to completion
  job_end = 0
  for i in range(0, iCPU['add']['cycles']-1):
    job_end = cpu1.run_cycle((None, False), CDB, (None, False), status)
    print("job_end : ", job_end)
    cpu1.log_state()
  # ack task end
  # job_end should be 1 now
  cpu1.ack_task_end()
  print("\nShould have made FU idle!")
  cpu1.log_state()
  print("======Ending add execution======")

  # Trying to run incorrect task results in no run on the FU
  # evident from no change in state of the accelerator apart from cycle
  # increment
  cpu1.run_cycle((task3, True), CDB, (None, False), status)
  cpu1.log_state()

  # Should get an error message
  # Trying to create undefined FU
  cpu_nor_tfu = FunctionalUnit('abcd', 10)

