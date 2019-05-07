"""

    This is a block that checks the type of task that is coming in, uses MemoryTrack object to determine
    the dependency. It takes care of branches and loops. There is a register file structure here as well.
"""
import sys
from helpers import check_branch
from TLB import TLB

class TaskDispatch:


    def __init__(self, speculating = False, TLB_size = None):

        # In case of an un-resolved if block, you have to stall
        self.stall = 0

        # This is to ignore the one extra decoded instruction that comes in case of jumps
        self.ignore = 0

        #This is to forbid the fetch unit from clearing its buffer (in case of loops/jumps)
        self.fetch_clear = 0

        # Flag for speculative portion
        self.speculative_ex = 0

        #Id for speculation TODO: wrap around
        self.spec_ID = 0

        #Predicted branch direction
        self.predict = 'not_taken'

        # Return PC in case of wrong prediction
        self.return_pc = 0

        # List of tasks to abort in case of wrong speculation
        self.tasks_to_abort = []

        # Stack to maintain loop PC
        self.loop_stack = []

        # We wait on these tasks
        self.wait_tasks = []

        # If speculating
        self.SPECULATING = speculating

        # Signifies the end of program
        self.end = False

        # FOr CDB
        self.CDB = None

        if self.SPECULATING:
            assert (TLB_size != None), "We are speculating!! Please provide speculation memory size"
            self.speculation_buffer = TLB(TLB_size, 900)

    def run_cycle(self, MemTrack, regTrack, task, pc, regfile, CDB):

        """
            This function takes in the decoded task and the memory tracker, and outputs
            the task to the correct reservation stations.

            This is like  a combinational logic.
            Input:
               MemTrack : Memory track object to keep track of dependency
               regTrack : Tracks the usage of registers (akin to scoreboard)
               task     : (task_dict, valid)
               pc       : Program counter (current)
               CDB      : (FU_name, FU_id, task_ID, result, dest, valid)
            Returns:
                pc_next     : In case there is a branch, this shows the next PC
                fetch_clear : this signal is for Fetch unit to point that it can clear the previous instructions
                stall       : This is to tell the processor to stall the execution unit
                out_task    : (task_dict, (dependent_task_id0,dependent_task_id1) , valid)
        """

        # These are the return values
        pc_next     = (None, 0)
        task_next   = (None, None, 0)
        task_to_abort = (None, 0)
        self.CDB = CDB
        print("DEBUG", self.loop_stack)

        ##### NOTES ######

        # 1. Take the input task and inform the Memory Tracker that you're going to write
        # somewhere and check the dependencies for the sources.
        # 2. Only control tasks are performed here (branches, jumps and loops)
        # Rest will be forwarded to the reservation stations.
        # 3. Speculation is static.

        # For valid CPU Instructions -  when pipeline is not stalled
        if(not(self.stall) and task[1] and task[0]['instrType']=='CPU'):

            # This generally happens in a cycle post the branch. If the branch was taken, then the
            # task that came from fetch is a step ahead and has to be ignored.
            if(self.ignore > 0):
                self.ignore -= 1

            ## Loop start instruction (Nothing to do, save the PC and wait till the loop-end comes)
            elif(task[0]['accelerator'] == 'lbeg'):

                # Expected format - lbeg <jump offset> <iter_reg> <num_iter>
                isRegS0, src0 = parseOperand(task[0]['src0'],0, task[0]['control'])
                isRegS1, src1 = parseOperand(task[0]['src1'],1, task[0]['control'])
                isRegD0, dst0 = parseOperand(task[0]['dst0'],2, task[0]['control'])

                in_operands = ([isRegS0, src0],[isRegS1, src1],[isRegD0, dst0])

                # Unfortunately, if there is a dependency unresolved here, we will need to stall.
                # In the future, we may be able to speculate, since this is also a branch.
                dependencyList = checkDependencyReg(regfile,regTrack,CDB,in_operands)

                # If there is no dependency, we are in the green - else we stall.
                if(any(dependencyList)):
                    self.stall      = 1
                    self.return_pc  = pc-1
                    self.wait_tasks = []
                    self.ignore     = 1

                    # Create a wait task list that contains tuples of (dependent task ID, src reg/mem)
                    for idx,tid in enumerate(dependencyList):
                        if(tid != None):
                            self.wait_tasks.append((tid, in_operands[idx][1]))

                # No need to wait
                else:
                    print("WE CONTINUE TO LOOP")
                    jump_offset = regfile.read(src0) if(isRegS0) else src0
                    num_iter    = regfile.read(src1) if(isRegS1) else src1
                    iter_reg    = regfile.read(dst0) if(isRegD0) else dst0

                    # Evaluate the condition: If passed, start the loop, else jump to the end of the loop
                    condition   = (iter_reg == num_iter)
                    if(condition):
                        # We jump to the offset requested by the user
                        pc_next     = (pc + -1 + jump_offset, 1)
                        self.ignore = 1
                    else:
                        # Write the PC
                        self.loop_stack.append(pc-1)
                        #Till the loop ends, you can not clear the fetch buffer
                        self.fetch_clear += 1
            ## Loop end instruction
            elif(task[0]['accelerator'] == 'lend'):

                # Simply go back to loop begin by popping the stack
                pc_next     = (self.loop_stack.pop(), 1)
                self.ignore = 1

            # Branch instructions : they follow similar routine as the loop begin (which was basically a beq
            # instruction)
            elif(task[0]['accelerator'][0] == 'b'):

                # Expected format - b** <jump offset> <src0>> <src1>
                branch = task[0]['accelerator']

                isRegS0, src0 = parseOperand(task[0]['src0'],0, task[0]['control'])
                isRegS1, src1 = parseOperand(task[0]['src1'],1, task[0]['control'])
                isRegD0, dst0 = parseOperand(task[0]['dst0'],2, task[0]['control'])

                in_operands = ([isRegS0, src0],[isRegS1, src1],[isRegD0, dst0])

                # Unfortunately, if there is a dependency unresolved here, we will need to stall.
                # In the future, we may be able to speculate, since this is also a branch.
                dependencyList = checkDependencyReg(regfile,regTrack,CDB,in_operands)

                # If there is no dependency, we are in the green - else we stall.
                if(any(dependencyList)):
                    self.stall      = 1
                    self.return_pc  = pc-1
                    self.wait_tasks = []
                    self.ignore     = 1

                    # Create a wait task list that contains tuples of (dependent task ID, src reg/mem)
                    for idx,tid in enumerate(dependencyList):
                        if(tid != None):
                            self.wait_tasks.append((tid, in_operands[idx][1]))
                else:

                    jump_offset = regfile.read(src0) if(isRegS0) else src0
                    src1        = regfile.read(src1) if(isRegS1) else src1
                    src2        = regfile.read(dst0) if(isRegD0) else dst0

                    if(branch == 'beq'):
                        condition = (src1 == src2)
                    elif(branch == 'bne'):
                        condition = (src1 != src2)
                    elif(branch == 'bge'):
                        condition = (src1 >= src2)
                    elif(branch == 'ble'):
                        condition = (src1 <= src2)
                    else:
                        sys.exit("Branch statement not understood")

                    # Branch off if condition satisfied
                    if(condition):
                        # We jump to the offset requested by the user
                        pc_next     = (pc -1 + jump_offset, 1)
                        self.ignore = 1

            elif(task[0]['accelerator'] == 'jmp'):

                # Format jmp <offset>
                isRegS0, src0 = parseOperand(task[0]['src0'],0, task[0]['control'])

                in_operands = ([isRegS0, src0],)

                # Check if the dependency
                dependencyList = checkDependencyReg(regfile,regTrack,CDB, in_operands)

                # If there is no dependency, we are in the green - else we stall.
                if(any(dependencyList)):
                    self.stall      = 1
                    self.return_pc  = pc-1
                    self.wait_tasks = []
                    self.ignore     = 1

                    # Create a wait task list that contains tuples of (dependent task ID, src reg/mem)
                    for idx,tid in enumerate(dependencyList):
                        if(tid != None):
                            self.wait_tasks.append((tid, in_operands[idx][1]))

                else:
                    jump_offset = regfile.read(src0) if(isRegS0) else src0
                    # We jump to the offset requested by the user
                    pc_next     = (pc -1 + jump_offset, 1)
                    self.ignore = 1

            elif(task[0]['accelerator'] == 'mov' or task[0]['accelerator'] == 'lw' or task[0]['accelerator'] == 'sw'):

                # format mov <src> <dst>
                instr = task[0]['accelerator']

                isRegS0, src0 = parseOperand(task[0]['src0'],0, task[0]['control'])
                isRegD0, dst0 = parseOperand(task[0]['src1'],1, task[0]['control'])

                in_operands  = [[isRegS0,src0]]
                out_operands = [dst0]

                dependencyList = checkDependencyReg(regfile,regTrack,CDB, in_operands)

                _ = regTrack.run_cycle((0,0,0,0,0,0),regfile, (0,0,0), (task[0]['task_id'], dst0, 1))

                task_dict = task[0]
                operands = {'in':[], 'out':out_operands}

                # Populate the input operands
                for idx,op in enumerate(in_operands):
                    # If the operand has a dependency, then the entry: (True, dependent task ID)
                    # Else: (False, Value)
                    isReg, src = op
                    if(dependencyList[idx] == None):
                        operands['in'].append((False, regfile.read(src) if(isReg) else src))
                    else:
                        operands['in'].append((True, dependencyList[idx]))

                task_next = (task[0], operands, 1)

            elif(task[0]['accelerator'] == 'end'):
                print("TEST COMPLETION RECEIVED!")
                self.end = True

            ## ** NORMAL Instructions  ** ##
            else:

                #<instr> <src0> <src1> <dst0>
                instr = task[0]['accelerator']

                isRegS0, src0 = parseOperand(task[0]['src0'],0, task[0]['control'])
                isRegS1, src1 = parseOperand(task[0]['src1'],1, task[0]['control'])
                isRegD0, dst0 = parseOperand(task[0]['dst0'],2, task[0]['control'])
                assert (isRegD0 == True), "In Arith instruction {0}, destination has to be a register".format(instr)

                in_operands  = [[isRegS0, src0],[isRegS1, src1]]
                out_operands = [dst0]

                dependencyList = checkDependencyReg(regfile,regTrack,CDB, ([isRegS0, src0],[isRegS1, src1]))
                # We need to inform the reg trackt thaat we will be updating the dest
                _ = regTrack.run_cycle((0,0,0,0,0,0),regfile, (0,0,0), (task[0]['task_id'], dst0, 1))


                ### CREATE A PACKAGE TO SEND TO RESERVATION STATION
                task_dict = task[0]
                operands = {'in':[], 'out':out_operands}

                # Populate the input operands
                for idx,op in enumerate(in_operands):
                    # If the operand has a dependency, then the entry: (True, dependent task ID)
                    # Else: (False, Value)
                    isReg, src = op
                    if(dependencyList[idx] == None):
                        operands['in'].append((False, regfile.read(src) if(isReg) else src))
                    else:
                        operands['in'].append((True, dependencyList[idx]))

                task_next = (task[0], operands, 1)
                # Ship this off to the reservation station


        # For valid TFU Instructions -  when pipeline is not stalled
        elif(not(self.stall) and task[1] and task[0]['instrType']=='TFU'):

            # This generally happens in a cycle post the branch. If the branch was taken, then the
            # task that came from fetch is a step ahead and has to be ignored.
            if(self.ignore > 0):
                self.ignore -= 1

            else:
                #<instr> <src0> <src0_size> <src1><src1><src1_size><dst0><dst0_size>
                instr = task[0]['accelerator']

                isRegS0, src0           = parseMemOperand(task[0]['inp0_mem'],0, task[0]['control'])
                isRegS01, src0_size     = parseMemOperand(task[0]['inp0_size'],1, task[0]['control'])
                isRegS1, src1           = parseMemOperand(task[0]['inp1_mem'],2, task[0]['control'])
                isRegS11, src1_size     = parseMemOperand(task[0]['inp1_size'],3, task[0]['control'])
                isRegD0, dst0           = parseMemOperand(task[0]['out0_mem'],4, task[0]['control'])
                isRegD01, dst0_size     = parseMemOperand(task[0]['out0_size'],5, task[0]['control'])

                in_operands  = [[isRegS0, src0],[isRegS01, src0_size],[isRegS1, src1], [isRegS11, src1_size],[dst0,
                                                                                                              dst0_size]]
                dependencyList = checkDependencyReg(regfile,regTrack,CDB, in_operands)

                # If there is no dependency, we are in the green - else we stall.
                if(any(dependencyList)):
                    self.stall      = 1
                    self.return_pc  = pc-1
                    self.wait_tasks = []
                    self.ignore     = 1

                    # Create a wait task list that contains tuples of (dependent task ID, src reg/mem)
                    for idx,tid in enumerate(dependencyList):
                        if(tid != None):
                            self.wait_tasks.append((tid, in_operands[idx][1]))

                else:
                    inp0_mem    = regfile.read(src0) if(isRegS0) else src0
                    inp0_size   = regfile.read(src0_size) if(isRegS01) else src0_size
                    inp1_mem    = regfile.read(src1) if(isRegS1) else src1
                    inp1_size   = regfile.read(src1_size) if(isRegS11) else src1_size
                    out0_mem    = regfile.read(dst0) if(isRegD0) else dst0
                    out0_size   = regfile.read(dst0_size) if(isRegD01) else dst0_size

                    # Now check for memory address dependencies
                    in_mems = [inp0_mem, inp1_mem]
                    out_mems = [out0_mem]

                    ### CREATE A PACKAGE TO SEND TO RESERVATION STATION
                    task_dict = task[0]
                    operands = {'in':[], 'out':out_mems}

                    # Populate the input operands
                    for idx,in_mem in enumerate(in_mems):
                        # If the operand has a dependency, then the entry: (True, dependent task ID)
                        # Else: (False, Value)
                        depTaskID, _ = MemTrack.run_cycle((0,0,0,0,0,0),(task[0]['task_id'],in_mem,1), (0,0,0))
                        if(depTaskID != None):
                            operands['in'].append((True,depTaskID))
                        else:
                             operands['in'].append((False, in_mem))

                    task_next = (task[0], operands, 1)
                    # Ship this off to the reservation station
                    # We need to inform the Mem trackt thaat we will be updating the dest
                    _ = MemTrack.run_cycle((0,0,0,0,0,0),(0,0,0), (task[0]['task_id'], out0_mem, 1))

        # If the pipeline is stalled because of a branch
        elif(self.stall):
            print(" Waiting for dependency resolution.")
            # Check if the CDB announced the data you were waiting for / Or if it got cleared in the RegFile/MemTrack
            wait_IDs = zip(*self.wait_tasks)[0]
            wait_src = zip(*self.wait_tasks)[1]

            # Check if CDB cleared
            CDB_cleared = CDB[5] and (CDB[2] in wait_IDs)
            if(CDB_cleared):
                CDB_clear_idx = wait_IDs.index(CDB[2])

            # Check if source reg was cleared
            reg_clear_check = checkDependency(regfile,regTrack, CDB, wait_src)
            reg_cleared = not(all(reg_clear_check))
            if(reg_cleared):
                reg_clear_idx = reg_clear_check.index(None)

            # Remove the entries whose dependencies were cleared
            if(CDB_cleared and reg_cleared):
                if(reg_clear_idx != CDB_clear_idx):
                    self.wait_tasks.pop(CDB_clear_idx)
                else:
                    self.wait_tasks.pop(CDB_clear_idx)
                    self.wait_tasks.pop(reg_clear_idx)
            elif(CDB_cleared):
                self.wait_tasks.pop(CDB_clear_idx)
            elif(reg_cleared):
                self.wait_tasks.pop(reg_clear_idx)

            # Now if the wait tasks list is empty, dependency is resolved.
            if(len(self.wait_tasks) == 0):
                print("Dependency resolved, jumping to: ", self.return_pc)
                # We set the pc to return_pc, and the execution will restart
                pc_next = (self.return_pc, 1)
                #Clear the Stall
                self.stall = 0
                self.ignore = 0

                #TODO: Instead of restarting, may be evaluate the condition here itself.

        # Update the Memory and Register trakcer with the CDB (Every cycle)
        _ = MemTrack.run_cycle(CDB, (None, None, 0), (None, None, 0))
        _ = regTrack.run_cycle(CDB,regfile, (0,0,0), (0, 0, 0))

        return pc_next, (self.fetch_clear == 0), (self.stall == 0), task_next, task_to_abort

    def speculation_resolve(self, CDB):
        """
            This function monitors the CDB constantly to see if the branch got resolved .
        """
        pc_next = (None, 0)

        print(" Speculative Execution.")
        # Check if the CDB announced the data you were waiting for / Or if it got cleared in the RegFile/MemTrack
        if(CDB[4] and (CDB[2] == self.dependency)):
            print(" Expected CDB task: %s, Received CDB task: %s . Resolution cleared!" % (self.dependency, CDB[2]))
            branch_taken = check_branch(self.branch,self.branch_target, CDB[3])
            speculation_succeed = (branch_taken and self.predict == 'taken') or (not branch_taken and self.predict == 'not_taken')

            if(speculation_succeed):
                print("Speculation success. Continue.")
            else:
                print("Speculation Failed. Returning.")
                # return to the start of the branch
                pc_next = self.return_pc
                self.ignore = 1

                #Clear the mappings and get a list of task IDs to abort
                self.tasks_to_abort = self.speculation_buffer.delete_entry(self.spec_ID, None)

            # ends the speculative execution
            self.speculative_ex = 0

        return pc_next


def parseOperand(operand, index, control):
    """
        Parses the operand, classifies whether it is an immediate or a register,
        also adds the sign.
    """
    # Register or immediate
    isReg = not(((0x01 << index)& control) == 0)
    isNeg = 1 if(((0x10 << index)&control) == 0) else -1
    data  = operand*isNeg

    return isReg, data

def parseMemOperand(operand, index, control):
    """
        Parses the operand, classifies whether it is an immediate or a register,
        also adds the sign.
    """
    # Register or immediate
    isReg = not(((0x1 << index)& control) == 0)
    data  = operand

    return isReg, data

def checkDependencyReg(regfile,regTrack, CDB, operands):
    """
        Checks the dependency of each operand, and returns a list of dependencies.
    """
    # Return List
    depList     = []
    # GO through every source operand
    for valid, op in operands:
        # Only if the operand is a register, we check for dependency
        if(valid):
            depTask = regTrack.run_cycle(CDB=(0,0,0,0,0,0), regFile=regfile, dispatch_req=(None,op,1),
                                              dispatch_info=(0,0,0))[0]

            if(CDB[-1] and (depTask!=None)):
                if(CDB[2] != depTask):
                    depList.append(depTask)
                else:
                    depList.append(None)
            else:
                depList.append(depTask)

        else:
            depList.append(None)

    return depList

def checkDependency(regfile,regTrack, CDB, operands):
    """
        Checks the dependency of each operand, and returns a list of dependencies.

        Same as the function above, but without a valid.
    """

    # Return List
    depList     = []
    # GO through every source operand
    for op in operands:
        # Only if the operand is a register, we check for dependency
        depTask = regTrack.run_cycle(CDB=(0,0,0,0,0,0), regFile=regfile, dispatch_req=(None,op,1),
                                              dispatch_info=(0,0,0))[0]

        depList.append(depTask)

    return depList



def checkDependencyMem(memTrack, operands):
    """
        Checks the dependency of each operand, and returns a list of dependencies.
    """
    depList     = []
    for idx,(valid, op) in enumerate(operands):
        if(valid):
            depList.append(regTrack.run_cycle(CDB=(0,0,0,0,0,0), regFile=regfile, dispatch_req=(None,op,1),
                                              dispatch_info=(0,0,0))[0])
        else:
            depList.append(None)

    return depList

