#!/usr/bin/env python

import sys,os

"""
    This file is intended to list all the accelerators in the HPU

    Format for adding an accelerator = { 'name', 'acc ID', 'num cycles'}


    NOTE: If you want to add any instructions/TFUs, please do so here. Adhere to the format for TFU instructions and
    CPU instructions.

    [7:0]   Acc ID
    [23:8]  Input0 memory
    [31:24] Input0 Size
    [47:32] Input1 memory
    [55:48] Input1 Size
    [71:56] Output memory
    [79:72] Output size
    [87:80] Control - Optional
    [95:88] Task ID - Optional
    [99:96] Process ID - Optional

    OPCODE Format for CPU

    [7:0]   Instr ID
    [23:8]  src0
    [39:24] src1
    [55:40] dst0
    [63:56] control - Optional

    Reference CPU - Intel SandyBridge
    source for CPU cycle numbers - https://www.agner.org/optimize/instruction_tables.pdf
"""

## Import TFU objects

iTFU = {
                'real_fir'      : {'count' : 1, 'ID' : [0],'instance':[None], 'cycles': 921},
                'complex_fir'   : {'count' : 1, 'ID' : [1],'instance':[None], 'cycles': 3696},
                'adaptive_fir'  : {'count' : 1, 'ID' : [2],'instance':[None],  'cycles': 4384},
                'iir'           : {'count' : 1, 'ID' : [3],'instance':[None],  'cycles': 2450},
                'vector_dot'    : {'count' : 1, 'ID' : [4],'instance':[None],  'cycles': 53},
                'vector_add'    : {'count' : 1, 'ID' : [5],'instance':[None],  'cycles': 131},
                'vector_max'    : {'count' : 1, 'ID' : [6],'instance':[None],  'cycles': 55},
                'fft_256'       : {'count' : 1, 'ID' : [7],'instance':[None],  'cycles': 18763},
                'dct_64'        : {'count' : 1, 'ID' : [8],'instance':[None],  'cycles': 874},
                'correlation'   : {'count' : 1, 'ID' : [9],'instance':[None],  'cycles': 753},
                'lud_dia'       : {'count' : 1, 'ID' : [10],'instance':[None],  'cycles': 912},
                'lud_perirow'   : {'count' : 1, 'ID' : [11],'instance':[None],  'cycles': 480},
                'lud_pericolm'  : {'count' : 1, 'ID' : [12],'instance':[None],  'cycles': 1280},
                'lud_internal'  : {'count' : 1, 'ID' : [13],'instance':[None],  'cycles': 512},
                'matmul'        : {'count' : 1, 'ID' : [14],'instance':[None],  'cycles': 256},
}

iCPU = {
                'lbeg'          : {'count' : 1, 'ID' : [16], 'instance':[None], 'cycles': 1},
                'lend'          : {'count' : 1, 'ID' : [17], 'instance':[None], 'cycles': 1},
                'mul'           : {'count' : 1, 'ID' : [18], 'instance':[None], 'cycles': 3},
                'sub'           : {'count' : 1, 'ID' : [19], 'instance':[None], 'cycles': 1},
                'div'           : {'count' : 1, 'ID' : [20], 'instance':[None], 'cycles': 20},
                'add'           : {'count' : 1, 'ID' : [21], 'instance':[None], 'cycles': 1},
                'fmul'          : {'count' : 1, 'ID' : [22], 'instance':[None], 'cycles': 5},
                'fsub'          : {'count' : 1, 'ID' : [23], 'instance':[None], 'cycles': 1},
                'fdiv'          : {'count' : 1, 'ID' : [24], 'instance':[None], 'cycles': 25},
                'fadd'          : {'count' : 1, 'ID' : [25], 'instance':[None], 'cycles': 3},
                'mov'           : {'count' : 1, 'ID' : [26], 'instance':[None], 'cycles': 1},
                'jmp'           : {'count' : 1, 'ID' : [27], 'instance':[None], 'cycles': 1},
                'beq'           : {'count' : 1, 'ID' : [28], 'instance':[None], 'cycles': 1},
                'bne'           : {'count' : 1, 'ID' : [29], 'instance':[None], 'cycles': 1},
                'ble'           : {'count' : 1, 'ID' : [30], 'instance':[None], 'cycles': 1},
                'bge'           : {'count' : 1, 'ID' : [31], 'instance':[None], 'cycles': 1},
                'lw'            : {'count' : 1, 'ID' : [32], 'instance':[None], 'cycles': 10},
                'sw'            : {'count' : 1, 'ID' : [33], 'instance':[None], 'cycles': 10},
                'end'           : {'count' : 1, 'ID' : [34], 'instance':[None], 'cycles': 10},
                'cmp'           : {'count' : 1, 'ID' : [35], 'instance':[None], 'cycles': 1},
                'load_tile'           : {'count' : 1, 'ID' : [36], 'instance':[None], 'cycles': 10},
                'store_tile'           : {'count' : 1, 'ID' : [37], 'instance':[None], 'cycles': 10}
        }


instr_encode = {  # TFUs
                'real_fir'    :  0,
                'complex_fir' :  1,
                'adaptive_fir':  2,
                'iir'         :  3,
                'vector_dot'  :  4,
                'vector_add'  :  5,
                'vector_max'  :  6,
                'fft_256'     :  7,
                'dct_64'      :  8,
                'correlation' :  9,
                'lud_dia'     :  10,
                'lud_perirow' :  11,
                'lud_pericolm':  12,
                'lud_internal':  13,
                'matmul'      :  14,

                # CPU Instructions
                'lbeg'        : 16,
                'lend'        : 17,
                'mul'         : 18,
                'sub'         : 19,
                'div'         : 20,
                'add'         : 21,
                'fmul'        : 22,
                'fsub'        : 23,
                'fdiv'        : 24,
                'fadd'        : 25,
                'mov'         : 26,
                'jmp'         : 27,
                'beq'         : 28,
                'bne'         : 29,
                'ble'         : 30,
                'bge'         : 31,
                'lw'          : 32,
                'sw'          : 33,
                'end'         : 34,
                'cmp'         : 35,
                'load_tile'   : 36,
                'store_tile'   : 37
                }

instr_decode = {
                   0 : 'real_fir'    ,
                   1 : 'complex_fir' ,
                   2 : 'adaptive_fir',
                   3 : 'iir'         ,
                   4 : 'vector_dot'  ,
                   5 : 'vector_add'  ,
                   6 : 'vector_max'  ,
                   7 : 'fft_256'     ,
                   8 : 'dct_64'      ,
                   9 : 'correlation' ,
                   10:    'lud_dia'       ,
                   11:    'lud_perirow'   ,
                   12:    'lud_pericolm'  ,
                   13:    'lud_internal'  ,
                   14:    'matmul'  ,

                  16 : 'lbeg'        ,
                  17 : 'lend'        ,
                  18 : 'mul'         ,
                  19 : 'sub'         ,
                  20 : 'div'         ,
                  21 : 'add'         ,
                  22 : 'fmul'        ,
                  23 : 'fsub'        ,
                  24 : 'fdiv'        ,
                  25 : 'fadd'        ,
                  26 : 'mov'         ,
                  27 : 'jmp'         ,
                  28 : 'beq'         ,
                  29 : 'bne'         ,
                  30 : 'ble'         ,
                  31 : 'bge'         ,
                  32 : 'lw'          ,
                  33 : 'sw'          ,
                  34 : 'end'         ,
                  35:  'cmp'         ,
                  36:  'load_tile'   ,
                  37:  'store_tile'
                }

"""
accelerator_decode = {
                '0' : 'real_fir',
                '1' : 'complex_fir',
                '2' : 'adaptive_fir',
                '3' : 'iir',
                '4' : 'vector_dot',
                '5' : 'vector_add',
                '6' : 'vector_max',
                '7' : 'fft_256',
                '8' : 'dct_64',
                '9' : 'correlation',
                '10' : 'lbeg',
                '11' : 'lend',
                '12' : 'mul',
                '13' : 'add',
                '14' : 'mov',
                '15' : 'if',
                '16' : 'jmp',
                '17' : 'real_fir',
                '18' : 'complex_fir',
                '19' : 'adaptive_fir',
                '20' : 'iir',
                '21' : 'vector_dot',
                '22' : 'vector_add',
                '23' : 'vector_max',
                '24' : 'fft_256',
                '25' : 'dct_64',
                '26' : 'correlation',
                '27' : 'real_fir',
                '28' : 'complex_fir',
                '29' : 'adaptive_fir',
                '30' : 'iir',
                '31' : 'vector_dot',
                '32' : 'vector_add',
                '33' : 'vector_max',
                '34' : 'fft_256',
                '35' : 'dct_64',
                '36' : 'correlation'
                }
"""
# Misc

# Create a unified dict
accelerators = dict(iTFU)
accelerators.update(iCPU)

total_accelerators_count = 0
res_station_size = dict()

# Each FU should get 4 (effective) entries in the reservation station
for key in accelerators.keys():
    count = accelerators[key]['count']
    total_accelerators_count += count
    res_station_size[key] = count * 4

