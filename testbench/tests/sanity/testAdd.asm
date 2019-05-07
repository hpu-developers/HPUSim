; This test verifies execution of add operation in the ISA
; reg-reg ops
; R1 = 32, R2 = 16
mov #32 R1
mov #16 R2
; R3 = R1 + R2
add R1 R2 R3
end
