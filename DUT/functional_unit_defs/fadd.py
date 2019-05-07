"""
  This module implements a floating point adder.
"""
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from accelerators import iCPU, iTFU
from functional_unit import FunctionalUnit

class FPAdder(FunctionalUnit):
  """
  class for simulating an adder
  """
  def run_new_task_if_given(self, task):
    """
    This initiates execution of new addition on the functional unit and runs a cycle
    for it. We assume no cycles are required for task setup.

    Args:
      task: task dictionary or null

    Return:
      None
    """
    if((task is not None) and (task['accelerator'] == self.name)):
      # setup task execution
      ## perform fp addition
      if((task['data']['in'][0] is not None) and (task['data']['in'][0] is not None)):
          self.result = task['data']['in'][0] + task['data']['in'][1]
      task['result'] = self.result
      self.result_dst = task['data']['out'][0]
      task['dest'] = self.result_dst
      ## debug
      print("Performing addition in fpadder!")
      self.task_counter = iCPU[self.name]['cycles'] - 1
      self.busy = 1
      self.task = task
    else:
      self.busy = 0

    return None

if __name__ == "__main__":

  from acc_status import AccStatus
  from accelerators import *

  # create an integer addition task
  task1 = { 'accelerator' : 'fadd',
            'inp_mem'     : 0,
            'inp_size'    : 1800,
            'out_mem'     : 2000,
            'out_size'    : 1000,
            'task_id'     : 0,
            'pid'         : 0,
            'data'        : {'in': [1.0,2.0], 'out': [3]}
          }
  iadder = FPAdder('fadd', 25)
  CDB = (None, None, None, None, None, 0)
  status = AccStatus(total_accelerators_count)
  iadder.run_cycle((None, False), CDB, (None, False), status)
  iadder.log_state()

  print("======Starting add execution======")
  # Run task 1
  iadder.run_cycle((task1, True), CDB, (None, False), status)
  iadder.log_state()
  # Run task 1 to completion
  job_end = 0
  for i in range(0, iCPU['fadd']['cycles']-1):
    job_end = iadder.run_cycle((None, False), CDB, (None, False), status)
    print("job_end : ", job_end)
    iadder.log_state()
  # ack task end
  # job_end should be 1 now
  iadder.ack_task_end()
  print("\nShould have made FU idle!")
  iadder.log_state()
  print("======Ending add execution======")

