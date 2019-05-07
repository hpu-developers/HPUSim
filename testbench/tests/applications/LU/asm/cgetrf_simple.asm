;n = 64
mov #40 R0 
;n*n 
mul R0 R0 R3
;i=0
mov #0 R1
;L matrix zeroed
; lw/sw 4Bytes
; Store 0 to L and U matrix ;TODO: Memory address
;for i=0;i<n*n;i++
lbeg #4 R1 R3
sw #0 #DEADBEAF
add R2 1 R2
lend
;i=0
mov #0 R1
; for i =0;i<n*n;i++
lbeg #4 R1 R3 
sw #0 #BEEFDEAD
add R2 #1 R2
lend
