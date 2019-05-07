This folder enumerates different test cases one can run to verify the functionality of our HTS.


| Test cases    | Naive |    Runtime    |    HTS        |
|               |  1/2  |   1    |  2   |  1   |  2     |
| ------------- |:-------------:| ---------------------:|
| apps_n_d      |69000  |42381  |23625  |37541 |18785   |
| apps_s_d      |69000  |42381  |42381  |37541 |18785   |
| apps_d_d      |69000  |42381  |23673  |37541 |18833   |
| apps_r_d      |69000  |42381  |23757  |37541 |18917   |
| apps_l_n_d    |47669  |23905  |23905  |18823 |18823   |
| apps_l_d      |47669  |23905  |23905  |18823 |18823   |
| apps_b_n_t_n_d|34795  |61391  |42625  |56309 |37543   |
| apps_b_t_n_d  |34795  |42625  |23869  |37543 |18787   |
| apps_b_t_d    |34795  |42625  |23869  |37543 |18787   |

Task Structure:
    Total               - 64 bits
    Supported max DRAM  - 4GB
    Min Block Size      - 64kB
    Max allocable blocks- 256
    Max allocable Size  - 8MB

    [3:0]   Acc ID (4 bits)
    [19:4]  Input memory (16 bits)
    [27:20] Input Size (8 bits)
    [43:28] Output memory (4 bits)
    [51:44] Output size (8 bits)
    [59:52] Task ID (8 bits)
    [63:60] Process ID (4 bits)
    [67:64] Control
    [127:68] Metadata

Note: 
    (a) We use hex notation in the apps*.asm file
    (b) Data is "block addressable"

Example tasks:
    (1) real_fir 10 2 13 2 0 0 0 0000
Decoded task:
    {    
        'accelerator': 'real_fir', 
        'inp_mem': '0010', // input memory location
        'inp_size': '02', 
        'out_mem': '0013', // output memory location
        'out_size': '02', 
        'task_id': '2', 
        'pid': '0',
        'control': '0',
        'metadata':'00000000000000' // acc-specific data
    }

    (2) lbeg 9 2 0 0 0 0 0 0001
 Decoded task:
     {
         'accelerator': 'lbeg',
         'inp_mem': '0009', // counter value
         'inp_size': '02', // register to be used for counter
         'out_mem': 'xxxx',
         'out_size': 'xx',
         'task_id': '0',
         'pid': '0',
         'control': '0',
         'metadata':'00000000000001' // acc-specific data
     }

     (3) lend 0 2 2 0 0 0 0 0001
  Decoded task:
      {
          'accelerator': 'lend',
          'inp_mem': 'xxxx',
          'inp_size': '02', // register to be used for counter (same as lbeg)
          'out_mem': '0002',
          'out_size': 'xx',
          'task_id': '0',
          'pid': '0',
          'control': '0',
          'metadata':'00000000000001' // acc-specific data
      }

      (4) add 2 6 8 0 0 0 0 0001 (same for mul)
  Decoded task:
      {
          'accelerator': 'add',
          'inp_mem': '0002', // operand 2 register
          'inp_size': '06', // operand 1 register
          'out_mem': '0008', // output register
          'out_size': 'xx',
          'task_id': '0',
          'pid': '0',
          'control': '0',
          'metadata':'00000000000001' // acc-specific data
      }

      (5) mov 4 0 6 0 0 0 0 0001
   Decoded task:
       {
           'accelerator': 'mov',
           'inp_mem': '0002', // control=0 ? immediate value : register
           'inp_size': 'xx',
           'out_mem': '0008', // output register
           'out_size': 'xx',
           'task_id': '0',
           'pid': '0',
           'control': '0', // 0 - immediate, 1 - read from regfile
           'metadata':'00000000000001' // acc-specific data
       }

       (6) if 93 a 12 0 1 0 d 0000
    Decoded task:
        {
            'accelerator': 'if',
            'inp_mem': '0093', // memory address for data to resolve branch
            'inp_size': '0a', // register for pc_jump
            'out_mem': '0012', // value for comparison
            'out_size': '00',
            'task_id': '1', // dependent load task
            'pid': '0',
            'control': 'd', // bne (branch type)
            'metadata':'00000000000000' // acc-specific data
        }

As of now, we do not consider overlap for dependency check.

apps_no_dependency.asm -> checks for execution of all kernels, with no dependencies, with each kernel having two instances => WORKS
apps_same_dependency.asm -> has dependency but only between similar tasks => WORKS
apps_diff_dependency.asm -> has dependency but only between different tasks => WORKS
apps_random_dependency.asm -> may/may not have dependency => WORKS
apps_loop_no_dependency.asm -> independent loop of tasks => WORKS
apps_loop_dependency.asm -> task inside loop construct is dependent on tasks before loop construct => SHOULD WORK
apps_branch_no_dependency.asm -> has a branch which should be taken => SHOULD WORK
apps_branch_dependency.asm -> has a branch which should be taken => SHOULD WORK
