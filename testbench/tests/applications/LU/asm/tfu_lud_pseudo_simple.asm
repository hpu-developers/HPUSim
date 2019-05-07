;allocate perirow, BS*BS
;
;loop_diag: for d=0; d < M/BS .. d++
;   allocate dialud, M*BS-d*BS*BS
;   
;   load_load: for i =0 .. M/BS - d .. i++
;        load_tile matrixaddr+d*BS*M+d*BS+i*BS, dialud+i*BS,M,BS
;   lud_dia   dialud, dialud, BS*BS
;
;   if(d!=M/BS-1)
;       load_tile matrixaddr+d*BS*M+BS*M, perirow,M,BS
;    
;       lud_perirow perirow, perirow, BS*BS 
;       
;       loop_pericolm: for c=1 .. (M/BS-d) .. c++
;             lud_pericolm dialud+c*BS, dialud+c*BS, BS*BS
;    
;            lud_internal perirow, dialud+c*BS, matrixaddr+d*BS*M+BS*M+c*BS, BS*BS
;            store_tile dialud+c*BS, matrixaddr+(d*BS*M)+c*BS, BS
;    
;   free dialud, M*BS-d*BS*BS
;
;mov src, dst
;mul src1,src2, dst
;lbeg ;loopcode,  itrvar, cond
;lend
;beq src1,src2, offset
;bne
;bge
;ble
;jump
;;loadtile src,dst, rowsize, TH, TW
;.parameters
;   .long BS  16
;   .long M   1024
;.code              

mov #10 R0
mov #40 R1
;mul srcA srcB dst BS*BS
mul R0 R0 R2
;allocate dst sizer:TODO:perirow
allocate #00000000 R45
;mov src dst
mov #0 R3
;div srcAsrcB dst M/BS
div R1 R0 R4
mov #0 R4
;end of file
mov #28 R25
;d_itr is in r5 r4 is cond 0x26
lbeg R25 R4 R5
;d*BS*BS
mul R5 R2 R6 
;M*BS
mul R1 R0 R7
;sub srcAsrcBdst --- ;M*BS-d*BS*BS 
sub R7 R6 R8
;load_load cond is in r9 M/BS-d
sub R4 R5 R9
;dialud
allocate #00080000 R8 

;load_load loop:
;i
mov #0 R10
mov #A0000000 R11
;d*BS*M
mul R7 R5 R12
;matrixadd+d*BS*M
add R12 R11 R13 
;d*BS
mul R5 R0 R14
;matrixadd+d*BS*M+d*BS
add R13 R14 R15

mov #7 R19
;R19-->PCOffset i -->R10 M/BS-d -->R9
lbeg R19 R9 R10 
;i*BS
mul R10 R0 R16
;dialud_i*BS
add #00080000 R16 R17
; matrixadd+d*BS*M+d*BS + i*BS
add R15 R16 R18
;loadtile srcdst rowsize TH TW

load_tile R18 R2 R17
;i++
add R10 #1 R10
lend

;lud_dia dialud dialud BS*BS
lud_dia #00080000 R0 #00080000 R0 #0008000 R0
;M/BS -1
sub R4 #1 R10
;if(d !=M/BS-1):TODO: offset
bne #10 R5 R10
;matrixaddr+d*BS*M+BS*M
add R13 R7 R19
;loadtile src perirow rowsize TH TW
load_tile R19 R2 R45 

lud_perirow R45 R0 R45 R0 R45 R0

;loop_pericolm:
mov #1 R20 
mov #10 R26
;R20 --> c M/BS-d --> R9
lbeg R26 R9 R20
;c*BS
mul R20 R0 R21 
;dialud+c*BS
add #00080000 R21 R22
lud_pericolm R22 R0 R22 R0 R22 R0
;matrixaddr+d*BS*M+BS*M+c*BS
add R21 R19 R23
lud_internal R45 R0 R22 R0 R23 R0
;matrixadd+d*BS*M+c*BS
add R13 R21 R24
store_tile R22 R2 R24
;c++
add R20 #1 R20
lend

;free the memory
free #000800000 R8
;d++
add R5 #1 R5
lend
