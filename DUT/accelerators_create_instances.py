"""
  This script creates instances of all the functional unit definitions we have,
  and adds those instances to CPU and TFU dictionaries present in accelerators.py.
  These instances are supposed to be used for calling any method on the corresponding FU
  instead of creating FunctionalUnit instances in simulation environment.

  NOTE: This is the script to be imported in order to access our accelerator definitions.

  Usage:
    from accelerators_create_instances import iCPU, iTFU
    ...
    iCPU['add']['instance'][0].run_cycle(...)
    iTFU['fft_256']['instance'][0].run_cycle(...)
"""

from accelerators import *
from functional_unit_defs import *
from functional_unit import *

#### CPU FUNCTIONAL UNITS ####

# create instances
adder = Adder('add', 21)
subtracter = Subtracter('sub', 19)
multiplier = Multiplier('mul', 18)
divider = Divider('div', 20)
fpadder = FPAdder('fadd', 25)
fpsubtracter = FPSubtracter('fsub', 23)
fpmultiplier = FPMultiplier('fmul', 22)
fpdivider = FPDivider('fdiv', 24)
load_1 = Load('lw', 32)
load_2 = LoadTile('load_tile', 36)
store_1 = Store('sw', 33)
store_2 = StoreTile('store_tile', 37)
mov = Mov('mov', 26)
compare = Compare('cmp', 35)

# store instances
iCPU['add']['instance'][0] = adder
iCPU['sub']['instance'][0] = subtracter
iCPU['mul']['instance'][0] = multiplier
iCPU['div']['instance'][0] = divider
iCPU['fadd']['instance'][0] = fpadder
iCPU['fsub']['instance'][0] = fpsubtracter
iCPU['fmul']['instance'][0] = fpmultiplier
iCPU['fdiv']['instance'][0] = fpdivider
iCPU['lw']['instance'][0] = load_1
iCPU['load_tile']['instance'][0] = load_2
iCPU['sw']['instance'][0] = store_1
iCPU['store_tile']['instance'][0] = store_2
iCPU['mov']['instance'][0] = mov
iCPU['cmp']['instance'][0] = compare

#### TASK FUNCTIONAL UNITS ####

# create instances
for accelerator in iTFU:
  iTFU[accelerator]['instance'][0] = FunctionalUnit(accelerator, iTFU[accelerator]['ID'][0])

if __name__ == "__main__":

  from accelerators import total_accelerators_count
  from acc_status import AccStatus

  CDB = (None, None, None, None, None, 0)
  status = AccStatus(total_accelerators_count)

  iCPU['add']['instance'][0].run_cycle((None, False), CDB, (None, False), status)
  iCPU['add']['instance'][0].log_state()

  iCPU['sub']['instance'][0].run_cycle((None, False), CDB, (None, False), status)
  iCPU['sub']['instance'][0].log_state()

  iCPU['mul']['instance'][0].run_cycle((None, False), CDB, (None, False), status)
  iCPU['mul']['instance'][0].log_state()

  iCPU['div']['instance'][0].run_cycle((None, False), CDB, (None, False), status)
  iCPU['div']['instance'][0].log_state()

  iCPU['fadd']['instance'][0].run_cycle((None, False), CDB, (None, False), status)
  iCPU['fadd']['instance'][0].log_state()

  iCPU['fsub']['instance'][0].run_cycle((None, False), CDB, (None, False), status)
  iCPU['fsub']['instance'][0].log_state()

  iCPU['fmul']['instance'][0].run_cycle((None, False), CDB, (None, False), status)
  iCPU['fmul']['instance'][0].log_state()

  iCPU['fdiv']['instance'][0].run_cycle((None, False), CDB, (None, False), status)
  iCPU['fdiv']['instance'][0].log_state()

  # load and store units' run_cycle have an extra input at the end
  # which connects them to the execution of their corresponding memory subsytems
  # (addr, cycles, valid)
  iCPU['lw']['instance'][0].run_cycle((None, False), CDB, (None, False), status, (None, 0, False))
  iCPU['lw']['instance'][0].log_state()

  iCPU['load_tile']['instance'][0].run_cycle((None, False), CDB, (None, False), status, (None, 0, False))
  iCPU['load_tile']['instance'][0].log_state()

  iCPU['sw']['instance'][0].run_cycle((None, False), CDB, (None, False), status, (None, 0, False))
  iCPU['sw']['instance'][0].log_state()

  iCPU['store_tile']['instance'][0].run_cycle((None, False), CDB, (None, False), status, (None, 0, False))
  iCPU['store_tile']['instance'][0].log_state()

  iCPU['mov']['instance'][0].run_cycle((None, False), CDB, (None, False), status)
  iCPU['mov']['instance'][0].log_state()

  iCPU['cmp']['instance'][0].run_cycle((None, False), CDB, (None, False), status)
  iCPU['cmp']['instance'][0].log_state()

  for accelerator in iTFU:
   iTFU[accelerator]['instance'][0].run_cycle((None, False), CDB, (None, False), status)
   iTFU[accelerator]['instance'][0].log_state()
