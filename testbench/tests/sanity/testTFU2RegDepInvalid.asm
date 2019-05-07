; This test verifies execution of basic DSP TFU operations in the ISA
; opcode in0 in0size in1 in1size out out0size control taskid processid

;problem size M
mov #40 R0 
;bs 
mov #10 R1 
;in0
mov #10000000 R2 
;in1
mov #20000000 R3 
;in2
mov #30000000 R4 
;itrs
div R0 R1 R5
;i
mov #0 R6
;loop - i=0 .. M/bs
lbeg #7 R5 R6
iir R2 R1 R3 R1 R4 R1
add R4 #1 R8
add R6 #1 R6
lw R8 R9 
mul R9 R1 R10
lend
end
