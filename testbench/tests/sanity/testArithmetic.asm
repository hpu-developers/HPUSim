; This test verifies execution of basic arithmetic operations in the ISA
; reg-reg ops
; R1 = 32, R2 = 16
mov #32 R1
mov #16 R2
; R3 = R1 + R2
add R1 R2 R3
; R4 = R1 - R2
sub R1 R2 R4
; R5 = R1 * R2
mul R1 R2 R5
; R6 = R1 / R2
div R1 R2 R6
; R7 = 32, R8 = 16
mov #32 R7
mov #16 R8
; R9 = R7 + R8
fadd R7 R8 R9
; R10 = R7 - R8
fsub R7 R8 R10
; R11 = R7 * R8
fmul R7 R8 R11
; R12 = R7 / R8
fdiv R7 R8 R12
; reg-immediate ops
; R1 = 64
mov #64 R1
; R3 = R1 + 4
add R1 #4 R3
; R4 = R1 - 4
sub R1 #4 R4
; R5 = R1 * 4
mul R1 #4 R5
; R6 = R1 / 4
div R1 #4 R6
; R7 = 64
mov #64 R7
; R8 = R7 + 4
fadd R7 #4 R8
; R9 = R7 - 4
fsub R7 #4 R8
; R10 = R7 * 4
fmul R7 #4 R10
; R11 = R7 / 4
fdiv R7 #4 R11

end
