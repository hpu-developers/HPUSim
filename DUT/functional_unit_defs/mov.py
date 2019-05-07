"""
  This module implements a mov funcional unit which would essentially writing src value into dst (result)
"""
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from accelerators import iCPU, iTFU
from functional_unit import FunctionalUnit

class Mov(FunctionalUnit):
  """
  class for simulating an adder
  """
  def run_new_task_if_given(self, task):
    """
    This initiates execution of new mov on the functional unit and runs a cycle
    for it. We assume no cycles are required for task setup.

    Args:
      task: task dictionary or null

    Return:
      None
    """
    # debug
    if((task is not None) and (task['accelerator'] == self.name)):
      # setup task execution
      ## perform mov
      self.result = task['data']['in'][0]
      task['result'] = self.result
      self.result_dst = task['data']['out'][0]
      task['dest'] = self.result_dst
      ## debug
      print("Performing mov op in mov!")
      self.task_counter = iCPU[self.name]['cycles'] - 1
      self.busy = 1
      self.task = task
    else:
      self.busy = 0

    return None

if __name__ == "__main__":

  from acc_status import AccStatus
  from accelerators import *

  # create a mov task
  # mov R0, R2
  task1 = { 'accelerator' : 'mov',
            'src0'        : 0,
            'src1'        : 0,
            'dst'         : 2,
            'control'     : 0,
            'data'        : {'in': [4], 'out': [3]}
          }
  iadder = Mov('mov', 26)
  CDB = (None, None, None, None, None, 0)
  status = AccStatus(total_accelerators_count)
  iadder.run_cycle((None, False), CDB, (None, False), status)
  iadder.log_state()

  print("======Starting mov execution======")
  # Run task 1
  iadder.run_cycle((task1, True), CDB, (None, False), status)
  iadder.log_state()
  # Run task 1 to completion
  job_end = 0
  for i in range(0, iCPU['mov']['cycles']-1):
    job_end = iadder.run_cycle((None, False), CDB, (None, False), status)
    print("job_end : ", job_end)
    iadder.log_state()
  # ack task end
  # job_end should be 1 now
  iadder.ack_task_end()
  print("\nShould have made FU idle!")
  iadder.log_state()
  print("======Ending mov execution======")

