; This test verifies execution of load_tile operation in the ISA
; load_tile <base_address> <size> <dst> => load_tile <src0> <src1> <dst>
; load 256, 260, 264, 268, 272, 276, 280, 284,  to scratchpad staring at 336 
mov #150 R1
load_tile #100 #20 R1
mov #100 R2
store_tile R1 #20 R2
end
