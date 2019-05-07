; This test verifies the execution of basic branch operation
; x = 10
; y = 20
; add_or_sub = 1
; if(add_or_sub == 0) {
;   z = x + y
; }else {
;   z = x - y
; }
; R1 = 10
mov #10 R1
; R2 = 20
mov #20 R2
; R3 = 1
mov #1 R3
; R4 = 2 (jump offset)
mov #2 R4
; R5 = 3 (branch offset)
mov #3 R5
beq R5 R3 #0
add R6 R1 R2
jmp R4
sub R6 R1 R2
mov #10 R7

end
