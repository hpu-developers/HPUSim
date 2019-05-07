; This test verifies the execution of basic loop operation
; run loop 10 times incrementing R1 by 5 each time
; x = 0
; for(int i=1;i<10;i++) {
;   x += 5
; }
; R1 = 0
mov #0 R1
; R2 = 4 (jump offset)
mov #4 R2
; R3 = 10 (number of iterations)
mov #10 R3
; R4 = 1 (loop register)
mov #1 R4
lbeg R2 R3 R4
add R1 #5 R1
add R4 #1 R4
lend
mov R6 #2 R6

end
