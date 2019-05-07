#!/usr/bin/env python

import sys,os
BASE = os.environ['BASE']
sys.path.insert(0, BASE+'/testbench/')
sys.path.insert(0, BASE+'/DUT/')
sys.path.insert(0, BASE+'/utils/')
sys.path.insert(0, BASE)

from task_fetch import TaskFetch
from parser import Parse
from task_decode import TaskDecode
from res_station import ResStation
from task_dispatch import TaskDispatch
from regfile import RegFile
from functional_unit import FunctionalUnit
from memory_track import MemoryTrack
from reg_track import regTrack
from acc_status import AccStatus
from control_cdb import ControlCDB
from cpu_memory_controller import CPUMemoryController
from shared_memory_controller import SharedMemoryController

from accelerators_create_instances import *

def main():

    # Create task stream coming from the CPU
    testbench = Parse(BASE+'/testbench/tests/sanity/testArithmetic.asm')
    # testbench = Parse(BASE+'/testbench/tests/sanity/testBranch.asm')
    # testbench = Parse(BASE+'/testbench/tests/sanity/testLoop.asm')
    # testbench = Parse(BASE+'/testbench/tests/sanity/testMemory.asm')
    # testbench = Parse(BASE+'/testbench/tests/sanity/testLoopMemory.asm')
    # testbench = Parse(BASE+'/testbench/tests/sanity/testTFU.asm')
    # testbench = Parse(BASE+'/testbench/tests/sanity/testLoadStoreSameLocation.asm')

    # TFU
    # testbench = Parse(BASE+'/testbench/tests/sanity/testTFU.asm')
    # testbench = Parse(BASE+'/testbench/tests/sanity/testReg2TFUDep.asm')
    # testbench = Parse(BASE+'/testbench/tests/sanity/testTFU2TFUDep.asm')
    # testbench = Parse(BASE+'/testbench/tests/applications/MM/asm/tfu_mm_noloadtile.asm')
    # testbench = Parse(BASE+'/testbench/tests/applications/LU/asm/tfu_lud_pseudo_simple_noloadtile.asm')
    # testbench = Parse(BASE+'/testbench/tests/sanity/testLoadTile.asm')

    # Applications
    # testbench = Parse(BASE+'/testbench/tests/applications/MM/asm/simple_mm.asm')
    # testbench = Parse(BASE+'/testbench/tests/applications/MM/asm/tiled_mm.asm')
    # testbench = Parse(BASE+'/testbench/tests/applications/LU/asm/cgetrf_lud_algorithm.asm')
    #Need two test case to complete the lud algorithm
    #testbench = Parse(BASE+'/testbench/tests/applications/LU/asm/cgetrf_lud_algorithm.asm')
    # testbench = Parse(BASE+'/testbench/tests/applications/LU/asm/cgetrf_lud_algorithm_secondhalf.asm')

    # Create a status log file
    original_stdout = sys.stdout
    sys.stdout = open("system.log","w+")
    print("\n\n========= SYSTEM LOG FILE =========\n\n")
    sys.stdout.close()
    sys.stdout = original_stdout
    print("========= START EXECUTION =========\n\n")
    print("Refer to system.log for cycle-wise status\n\n")

    taskIngress = []
    taskExgress = []

    # Create a list of all the accelerators
    accelerator_list = iCPU.keys()
    for a in iTFU.keys():
      accelerator_list.append(a)

    # Create a list of all accelerator IDs
    acc_id_list = []
    for a in accelerator_list:
        if((a in iCPU) and (a not in ['lbeg', 'lend', 'jmp', 'beq', 'bne', 'ble', 'bge', 'end'])):
          for Id in iCPU[a]['ID']:
            acc_id_list.append(Id)
        else:
          if((a not in ['lbeg', 'lend', 'jmp', 'beq', 'bne', 'ble', 'bge', 'end'])):
            for Id in iTFU[a]['ID']:
              acc_id_list.append(Id)

    print("Accelerators: ", acc_id_list, "\n\n")

    # Create task fetch unit
    fetch = TaskFetch(128)

    # Create Decode Unit
    decode = TaskDecode(32)

    # Create a dispatch Unit
    dispatch = TaskDispatch(speculating = False, TLB_size = 256)

    # Create the memory tracker
    memtrack = MemoryTrack(128)
    regtrack = regTrack()

    # Create a Register File
    regfile = RegFile(256)

    # Create accelerator status register
    status = AccStatus(total_accelerators_count)

    # Create reservation stations for all accelerators
    reservation_stations    = dict()
    for accelerator in accelerator_list:
        reservation_stations[accelerator] = ResStation(accelerator, res_station_size[accelerator])

    # Grab hold of instantiated accelerators
    all_accelerators = dict()
    for accelerator in accelerator_list:
        if(accelerator in iCPU):
            for index in range(0, len(iCPU[accelerator]['ID'])):
                all_accelerators[iCPU[accelerator]['ID'][index]] = iCPU[accelerator]['instance'][index]
        else:
            for index in range(0, len(iTFU[accelerator]['ID'])):
                all_accelerators[iTFU[accelerator]['ID'][index]] = iTFU[accelerator]['instance'][index]

    # MEM: Instantiate the controller for CPU Memory (L1 + L2 + DRAM)
    # instantiate a shared memory controller
    shmem_controller = SharedMemoryController()
    # instantiate a cpu memory controller
    cpumem_controller = CPUMemoryController(shmem_controller)

    # Instantiate the controller for cdb
    cdb_control = ControlCDB(1024)

    # Interface task stream with the task fetch stage
    # in a synchronous manner
    simulation_cycles   = 100000
    cycle_count         = 0

    # log prior state
    # redirect stdout to log file
    sys.stdout = open("system.log","a")
    print("----- HTS State -----")
    testbench.log_state()
    fetch.log_state()

    ## All the registers
    # (64-bit value, valid)
    task_to_decode      = (None, 0)
    task_to_decode_next = (None, 0)

    # task_dict
    decoded_task        = {}
    decoded_task_next   = {}

    # (task_dict, task_dependency, valid)
    task_to_dispatch = (None, None, 0)
    task_to_dispatch_next = (None, None, 0)

    # Create placeholder for the outputs
    accelerator_output_next = dict()
    accelerator_output = dict()

    # TODO can be optimized. don't need entire dict
    # (task_dict, valid)
    for Id in acc_id_list:
        accelerator_output_next[Id] = (None, 0)

    for Id in acc_id_list:
        accelerator_output[Id] = (None, 0)

    # Create placeholder for the inputs
    accelerator_input_next = dict()
    accelerator_input = dict()

    # TODO can be optimized. don't need entire dict
    # (task_dict, valid)
    for Id in acc_id_list:
        accelerator_input_next[Id] = (None, 0)

    for Id in acc_id_list:
        accelerator_input[Id] = (None, 0)

    # MEM: Create placeholder for CPU Memory controller responses
    cpu_read_resp_channel0 = (None, 0, False)
    cpu_read_resp_channel1 = (None, 0, False)
    cpu_cycles_resp_channel = ((None, 0, False), (None, 0, False), (None, 0, False), (None, 0, False))
    cpu_read_resp_channel0_next = (None, 0, False)
    cpu_read_resp_channel0_next = (None, 0, False)
    cpu_cycles_resp_channel_next = ((None, 0, False), (None, 0, False), (None, 0, False),(None, 0, False))
    # MEM: Create placeholder for Shared Memory controller responses
    shmem_read_resp_channel0 = (None, 0, False)
    shmem_read_resp_channel1 = (None, 0, False)
    shmem_cycles_resp_channel = ((None, 0, False), (None, 0, False), (None, 0, False), (None, 0, False))
    shmem_read_resp_channel0_next = (None, 0, False)
    shmem_read_resp_channel0_next = (None, 0, False)
    shmem_cycles_resp_channel_next = ((None, 0, False), (None, 0, False), (None, 0, False),(None, 0, False))

    # Create placeholder for status
    accelerator_status_next = dict()
    accelerator_status = dict()

    # valid
    for Id in acc_id_list:
        accelerator_status[Id] =  0

    for Id in acc_id_list:
        accelerator_status_next[Id] =  0


    # TODO implement early_ack for CDB
    # (FU_name, FU_Id, task_ID, valid)
    CDB = (None, None, None, None, None, 0)
    CDB_next = (None, None, None, None, None, 0)

    #
    # (task_ID, ack)
    ack = (None, 0)
    ack_next = (None, 0)

    pc = 0
    pc_next = 0
    jump = (None, 0)
    jump_next = (None, 0)
    stall = 0
    stall_next = 0
    fetch_clear = 0
    fetch_clear_next = 0
    # (task_id, valid)
    task_to_abort = (None, 0)
    task_to_abort_next = (None, 0)

    # For logging purposes
    finished_tasks = []
    tasks_rel_from_rs = []
    dispatched_tasks = []

    ## ****************** START THE RUN *************************##

    # We fill first 10 instructions into the queue to avoid cold misses. (Misses in instruction buffer isn't supported yet.)
    for i in range(10):

        # If the fetch buffer is not full, then load a task
        if(fetch.ready()):
            current_task = testbench.get_task()
        else:
            current_task = (None, 0)

        task_to_decode_next, pc_next = fetch.run_cycle(current_task, jump, decode_ready=False, clear_buffer=False) # clear_buffer=True)

    # TODO Run until all tasks are done
    while(cycle_count <= simulation_cycles):

        # redirect stdout to log file
        sys.stdout = open("system.log","a")

### Interface to TestBench ###

        # If the fetch buffer is not full, then load a task
        if(fetch.ready()):
            current_task = testbench.get_task()
        else:
            current_task = (None, 0)

        # Task format (task, valid)

### STAGE 1 : FETCH ###

        task_to_decode_next, pc_next = fetch.run_cycle(current_task, jump, stall, fetch_clear)

#### STAGE 2 : DECODE & DISPATCH #####

        # Input - task_to_decode, output - task_to_dispatch
        # print(task_to_decode)
        # Decode the task
        # TODO Always successful decode. Need to retain the value if unsuccessful
        decoded_task   = decode.run_cycle(task_to_decode)

        # Task to be dispatched
        # (task_dict, depedent_task_id, valid)
        # TODO right now there is direct connection between dispatch and FUs for abortion...can be modified to use CDB
        jump_next, fetch_clear_next, stall_next, task_to_dispatch_next, task_to_abort_next = dispatch.run_cycle(memtrack, regtrack, decoded_task, pc, regfile, CDB)


#### STAGE 3 : RESERVATION STATION ###

        # Input - task_to_dispatch, output - accelerator_input, accelerator_status

        # Reservation station updates
        for accelerator in accelerator_list:
            task_to_push, acc_id = reservation_stations[accelerator].run_cycle(task_to_dispatch, CDB, status, task_to_abort)
            if(accelerator in iCPU):
                for Id in iCPU[accelerator]["ID"]:
                    if acc_id is not None:
                        accelerator_input_next[acc_id] = task_to_push
                    else:
                        accelerator_input_next[Id] = (None, 0)
            else:
                for Id in iTFU[accelerator]["ID"]:
                    if acc_id is not None:
                        accelerator_input_next[acc_id] = task_to_push
                    else:
                        accelerator_input_next[Id] = (None, 0)


        # TaskBus that notes which accelerators are starting a new job
        for Id in acc_id_list:
            accelerator_status_next[Id] = accelerator_input_next[Id][1]

#### STAGE 4 : EXECUTE ##

        # Input - accelerator_input, accelerator_status, output - accelerator_output

        # Accelerator returns a 1 if it wants to finish and waits for acknowledgment on CDB
        # TODO can have a central ASR with FUs modifying it. Then we won't need to pass this status around
        for Id in acc_id_list:
            if(Id not in [32, 33, 36, 37]):
              accelerator_output_next[Id], status = all_accelerators[Id].run_cycle(accelerator_input[Id], CDB, task_to_abort, status)

        # MEM: Handle cpu lw and sw explicitly
        # load unit 1, ID: 32
        req, status = all_accelerators[32].run_cycle(accelerator_input[32], CDB, task_to_abort, status, cpu_cycles_resp_channel[0])
        accelerator_output_next[32] = (req[0], req[1])
        ## debug
        # print("LOAD accelerator_output_next: ", accelerator_output_next[32])

        # store unit 1, ID: 33
        req_1, status = all_accelerators[33].run_cycle(accelerator_input[33], CDB, task_to_abort, status, cpu_cycles_resp_channel[1])
        accelerator_output_next[33] = (req_1[0], req_1[1])
        ## debug
        # print("LOAD accelerator_output_next: ", accelerator_output_next[33])

        read_channel0 = req[2], req[3]
        read_channel1 = 0, 0
        write_channel0 = req_1[2], 0, req_1[3]
        write_channel1 = 0, 0, 0
        cpu_read_resp_channel0_next, cpu_read_resp_channel1_next, cpu_cycles_resp_channel_next = cpumem_controller.run_cycle(read_channel0, write_channel0, read_channel1, write_channel1)

        # MEM: Handle spad load_tile and store_tile explicitly
        # load_tile 1, ID:36
        req_2, status = all_accelerators[36].run_cycle(accelerator_input[36], CDB, task_to_abort, status, shmem_cycles_resp_channel[0])
        accelerator_output_next[36] = (req_2[0], req_2[1])

        # store_tile 1, ID: 37
        req_3, status = all_accelerators[37].run_cycle(accelerator_input[37], CDB, task_to_abort, status, shmem_cycles_resp_channel[1])
        accelerator_output_next[37] = (req_3[0], req_3[1])

        shmem_read_channel0 = req_2[2], req_2[3]
        shmem_read_channel1 = 0, 0
        shmem_write_channel0 = req_3[2], 0, req_3[3]
        shmem_write_channel1 = 0, 0, 0
        shmem_read_resp_channel0_next, shmem_read_resp_channel1_next, shmem_cycles_resp_channel_next = shmem_controller.run_cycle(shmem_read_channel0, shmem_write_channel0, shmem_read_channel1, shmem_write_channel1)


        # Update the statuses in ASR
        status.run_cycle(accelerator_status, CDB)

#### STAGE 5 : COMMIT ##

        # Input - accelerator_output, output - CDB

        # Pass the outputs of all the accelerator to the CDB Control and update the CDB
        # Note that only one of the accelerator's request is accepted and is broadcasted on CDB.
        # This is equivalent to commit.
        ## debug
        print("CDB accelerator_output: ", accelerator_output)
        CDB_next = cdb_control.run_cycle(accelerator_output)
        print("CDB_next: ", CDB_next)

        #TODO : Currently all the requests from accelerators are accepted. Change this to have
        # maximum outstanding requests. Rohit has implemented it in CDB control, use in top level.

        cycle_count += 1

        # log simulation results at the end of the cycle
        print("\n")
        print("----- Clock ", cycle_count, " -----")

        # Update all the variables at the end of the clock edge
        task_to_decode = task_to_decode_next
        task_to_dispatch  = task_to_dispatch_next
        accelerator_input = accelerator_input_next
        accelerator_status = accelerator_status_next
        accelerator_output = accelerator_output_next
        CDB = CDB_next
        pc = pc_next
        jump = jump_next
        stall = stall_next
        fetch_clear = fetch_clear_next
        task_to_abort = task_to_abort_next
        cpu_read_resp_channel0 = cpu_read_resp_channel0_next
        cpu_read_resp_channel1 = cpu_read_resp_channel1_next
        cpu_cycles_resp_channel = cpu_cycles_resp_channel_next
        shmem_read_resp_channel0 = shmem_read_resp_channel0_next
        shmem_read_resp_channel1 = shmem_read_resp_channel1_next
        shmem_cycles_resp_channel = shmem_cycles_resp_channel_next

        finished_task = [task for task in accelerator_output if (accelerator_output[task][1] == 1)]
        finished_tasks = finished_tasks.append(finished_task) if len(finished_tasks) is not 0 else finished_tasks

        if(decoded_task[0] == None and task_to_dispatch[0] != None):
            print(';' + str(cycle_count) + ' ' + str(task_to_dispatch[0]['accelerator']))
        elif(task_to_dispatch[0] == None and decoded_task[0]  != None):
            print(';' + str(cycle_count) + ' ' + str(decoded_task[0]['accelerator']) + ' ')
        elif(decoded_task[0]  != None and task_to_dispatch[0] != None):
            print(';' + str(cycle_count) + ' ' + str(decoded_task[0]['accelerator']) + ' ' + str(task_to_dispatch[0]['accelerator']))
        else:
            print(';' + str(cycle_count) + ' None')

        print("\n")
        # Print status
        print("\n STAGE 1 : fetched task - " + str(task_to_decode) + " PC: " + str(pc))
        print("\nSTAGE 2.1: Decoded task - ", decoded_task)
        print("\n STAGE 2 : dispatched task - " + str(task_to_dispatch) + " Stall: " + str(not stall) + " jump: " + str(jump))
        print("\n STAGE 3 : Tasks released from Reservation station - " + str([accelerator_input[task][0] for task in accelerator_input if (accelerator_input[task][1] == 1)]))
        print("\n STAGE 4 : Tasks that completed - " , finished_tasks)
        print("\n STAGE 5 : CDB broadcast - " + str(CDB))
        # print("\n The current status of each accelerator :" + str(status.get_all_status()))
        print("\n")
        regfile.log_state()
        #print("\n Current status of res_station")
        #for accelerator in accelerator_list:
        #    reservation_stations[accelerator].log_state()

        # LOGIC TO FINISH SIMULATION
        if(task_to_dispatch[1]):
            taskIngress.append(task_to_dispatch[0]['accelerator'])
        if(CDB[-1]):
            taskExgress.append(CDB[0])

        # Simulation is done if the dispatch unit has receieved End and exgress == ingress
        if(dispatch.end and (len(taskIngress) == len(taskExgress))):
            print("SIMULATION COMPLETED IN %d cycles" % cycle_count)
            sys.exit()

        print("INGRESS", len(taskIngress))
        print("EXGRESS", len(taskExgress))
        print("END HAS COME", dispatch.end)

        if(cycle_count > 1000):
             for accelerator in accelerator_list:
                 reservation_stations[accelerator].log_state()

        sys.stdout.close()
        sys.stdout = original_stdout

        # print to stdout if task completed
        for task in accelerator_output:
            if(accelerator_output[task][1] == 1):
                print("Task completed - ",accelerator_output[task][0]['task_id'], accelerator_output[task][0]['accelerator'] , "( cycle ", cycle_count, ")")


    # log simulation outputs
    sys.stdout = open("system.log","a")
    print("\n\n\n")
    print("----- HTS State -----")
    testbench.log_state()
    fetch.log_state()

    sys.stdout.close()
    sys.stdout = original_stdout
    print("\n\n========= END EXECUTION =========")

if __name__ == '__main__':
    main()
