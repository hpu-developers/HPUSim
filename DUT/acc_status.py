"""
    This file tracks the status of each of the accelerator in the system
"""

from accelerators import iTFU, iCPU

class AccStatus:

  def __init__(self, num_accelerators):
    self.num_accelerators  = num_accelerators
    self.accelerator_names = iTFU.keys()
    for instruction_names in iCPU.keys():
      self.accelerator_names.append(instruction_names)

    # Initialize all accelerators to be 0. Indexed by acc_ID
    self.status_reg = dict()
    for task in iTFU:
      for Id in iTFU[task]['ID']:
        self.status_reg[Id] = 0
    for instruction in iCPU:
      for Id in iCPU[instruction]['ID']:
        self.status_reg[Id] = 0

  def run_cycle(self, TaskInfBus, CDB):
    """
    Inputs
      - AccStatusBus : of length num accelerators and updated every cycle
      - TaskInfBus : of length num accelerators and updated every cycle
    """
    self.log_state()

    #### TODO turning iTFU check off for now

    for task in iTFU:
      for Id in iTFU[task]['ID']:
        if(TaskInfBus[Id] == 1):
          self.status_reg[Id] = 1
        elif((CDB[1] == Id) and (CDB[4]) == 1):
          self.status_reg[Id] = 0

    for instruction in iCPU:
      if instruction not in ['lbeg', 'lend', 'jmp', 'beq', 'bne', 'ble', 'bge', 'end']:
        for Id in iCPU[instruction]['ID']:
          if(TaskInfBus[Id] == 1):
            self.status_reg[Id] = 1
          elif((CDB[1] == Id) and (CDB[4]) == 1):
            self.status_reg[Id] = 0

  def check_status(self, acc_id):
    """
    Returns if the accelerator is busy or not
    """
    return self.status_reg[acc_id]

  def get_all_status(self):
    return self.status_reg

  def log_state(self):
    """
    Print the status
    """
    print("\n\n Accelerator Statuses: " + str(self.status_reg))

# Test TODO
if __name__ == '__main__':
  accstat = AccStatus(34)

  accelerator_status = dict()
  for Id in range(0,34):
    accelerator_status[Id] = 0
  CDB = (None, None, None, None, None, 0)
  accstat.run_cycle(accelerator_status, CDB)
  #accstat.log_state()

  accelerator_status[2] = 1
  accstat.run_cycle(accelerator_status, CDB)
  accstat.log_state()

  accelerator_status[2] = 0
  accelerator_status[15] = 1
  accstat.run_cycle(accelerator_status, CDB)
  accstat.log_state()

  CDB = (None, 2, None, None, None, 1)
  accstat.run_cycle(accelerator_status, CDB)
  accstat.log_state()

