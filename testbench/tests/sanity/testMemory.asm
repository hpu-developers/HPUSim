; This test verifies the execution of basic CPU memory operations
; R1 = mem(1234)
lw 1234 R1
; R2 = mem(1346)
lw 1346 R2
; R3 = R1 + R2
add R1 R2 R3
; mem(1456) = R3
mov #12 R4
sw R3 1456
sw R4 1200

end
