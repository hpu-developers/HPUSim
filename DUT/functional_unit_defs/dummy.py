"""
  This module implements a dummy FU/TFU for developer usage.
  If anyone wants to add a new HPU FU/TFU, he needs to modfiy class name, add his/her computation (compute + memory access)
  in run_new_task_if_given() method and consequently update the comments/print statements and test case class
  instantiation.
"""
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from functional_unit import FunctionalUnit

class Dummy(FunctionalUnit):
  """
  class for simulating a dummy
  """
  def run_new_task_if_given(self, task):
    """
    This initiates execution of new dummy on the functional unit and runs a cycle
    for it. We assume no cycles are required for task setup.

    Args:
      task: task dictionary or null

    Return:
      None
    """
    if((task is not None) and (task['accelerator'] == self.name)):
      # setup task execution
      #### PERFORM OP ####
      #### UPDATE result and result_dst fields ####
      #### STORE OUTPUT TO BE PUSHED TO CDB LATER ####
      task['result'] = self.result
      task['dest'] = self.result_dst
      ## debug
      print("Performing dummy operation in dummy FU!")
      self.task_counter = 0
      self.busy = 1
      self.task = task
    else:
      self.busy = 0

    return None

if __name__ == "__main__":

  from acc_status import AccStatus
  from accelerators import *

  # create an integer addition task
  task1 = { 'accelerator' : 'dummy',
            'inp_mem'     : 0,
            'inp_size'    : 1800,
            'out_mem'     : 2000,
            'out_size'    : 1000,
            'task_id'     : 0,
            'pid'         : 0
          }
  iadder = Adder('dummy', 15)
  CDB = (None, None, None, None, 0)
  status = AccStatus(total_accelerators_count)
  iadder.run_cycle((None, False), CDB, (None, False), status)
  iadder.log_state()

  print("======Starting dummy execution======")
  # Run task 1
  iadder.run_cycle((task1, True), CDB, (None, False), status)
  iadder.log_state()
  # Run task 1 to completion
  job_end = 0
  for i in range(0, CPU['dummy']['cycles']-1):
    job_end = iadder.run_cycle((None, False), CDB, (None, False), status)
    print("job_end : ", job_end)
    iadder.log_state()
  # ack task end
  # job_end should be 1 now
  iadder.ack_task_end()
  print("\nShould have made FU idle!")
  iadder.log_state()
  print("======Ending add execution======")

