; This test verifies the execution of cpu load followed by a store to the same location
; R1 = mem(1234)
mov 1234 R2
lw R2 R1
; mem(1456) = R3
sw R3 R2

end
