; This test verifies the execution of basic loop operation
; run loop 10 times incrementing R1 by 5 each time
; x = mem(1234)
; for(int i=1;i<10;i++) {
;   x += 5
; }

; R2 = 6 (jump offset)
mov #6 R2

; R3 = 10 (number of iterations)
mov #3 R3

; R4 = 1 (loop register)
mov #0 R4
mov #0 R7

lbeg #A #3 R7
; loop body
lbeg R2 R3 R4
lw #1234 R1
add R1 #5 R1
sw R1 #1600
add R4 #1 R4
lend
mov #0 R4
add R7 #1 R7
lend

mov R6 #2 R6
end
