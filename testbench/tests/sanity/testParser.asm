; This is to test if our decode works fine.
; As you add new instructions, add it here so that they are tested.
; CPU instructions
lbeg R0 R1 R2
lend
mul R1 R3 R5
sub #23 #-21 R1
div R2 #-12 R8
;TFU instructions
real_fir 0 0 0 0 0 0
vector_max 0 0 0 0 0 0 123 123 123

end
