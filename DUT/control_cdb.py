"""
  This file is required to allow several accelerators to simultaneoursly access CDB.
  Current naive version implements a ticket lock policy
  Compute Units send acks on a CDB and get the response based on the ticket number
"""

import random
import sys
from collections import deque

is_py2 = sys.version[0] == '2'
if is_py2:
  import Queue as queue
else:
  import queue as queue

from accelerators_create_instances import iCPU, iTFU

class ControlCDB:

  def __init__(self, MAX_TICKET_COUNT):

    self.MAX_TICKET_COUNT = MAX_TICKET_COUNT

    # Circular queue to store the tickets
    self.tickets = queue.Queue(maxsize=MAX_TICKET_COUNT)

  def run_cycle(self, reqs):
    """
      Each cycle, several acks can come, and one ack is sent

      Inputs:
        reqs - Requests for CDB broadcast from all accelerators (task, valid)
      Outputs:
        ack - THe fortunate person who got the ticket (accelerator, task_id, valid)
    """
    # Allocate a ticket if there is anything in the queue
    # This goes on the CDB
    return_ack, return_acc_id = self.process_ticket()

    # debug
    print("Task dict as read in control_cdb - ", return_ack)

    #Initialize ticket_alloc with False - These are requests
    ticket_allock = dict()
    #### TODO add loop for iTFU
    for accelerator in iCPU:
      if accelerator not in ['lbeg', 'lend', 'jmp', 'beq', 'bne', 'ble', 'bge', 'end']:
        for Id in iCPU[accelerator]["ID"]:
          ticket_allock[Id] = False

    for accelerator in iTFU:
      for Id in iTFU[accelerator]["ID"]:
        ticket_allock[Id] = False

    # If there are valid reqs, allocate
    for accelerator in iCPU:
      if accelerator not in ['lbeg', 'lend', 'jmp', 'beq', 'bne',  'ble', 'bge', 'end']:
        for Id in iCPU[accelerator]["ID"]:
          if(reqs[Id][1] == 1):
            # TODO Use this to send info back to FUs that their request has been processed and they can chill now
            ticket_allock[Id] = self.broadcast_ack(reqs[Id][0], Id)

    for accelerator in iTFU:
      for Id in iTFU[accelerator]["ID"]:
        if(reqs[Id][1] == 1):
          # TODO Use this to send info back to FUs that their request has been processed and they can chill now
          ticket_allock[Id] = self.broadcast_ack(reqs[Id][0], Id)

    # This goes on the CDB
    if(return_ack == None):
      return (None, None, None, None, None, 0)
    else:
      return (return_ack['accelerator'], return_acc_id, return_ack['task_id'], return_ack['result'], return_ack['dest'], 1)

  def broadcast_ack(self, task, acc_id):
    """
      Inputs:
      1. task : dict of the functional unit sending the ack

      Returns:
        True if ack received successfully, False otherwise
    """

    #TODO : Asssuming the overflow doesn't happen, to fix later

    # Check for overflow before adding a new ack
    if not self.tickets.full():
      self.tickets.put((task, acc_id))
      return True

    # OVERFLOW....FU should try again
    else:
      sys.exit("Control CDB buffer overflow")
      return False

  def process_ticket(self):
    """
      Processes the latest available ticket

      Returns:
        Id of FU if ticket is processed successfully, None otherwise
    """
    # UNDERFLOW...do nothing
    if self.tickets.qsize() == 0:
      return (None, None)

    return self.tickets.get()

  def get_current_tickets(self):
    """
      Returns a list of current pending tickets
    """

    return list(self.tickets)

  def reset_tickets(self):
    """
      Clears off all tickets. Hard Reset
    """

    self.tickets.clear()

if __name__ == "__main__":

  control = ControlCDB(128)

  for Id in range(129):
    if not control.broadcast_ack(Id, 10):
      print("Ticket Rejected")
  print("current pending tickets ", control.get_current_tickets())
  task_id = control.process_ticket()
  while task_id is not None:
    print(task_id, " processed")
    task_id = control.process_ticket()
