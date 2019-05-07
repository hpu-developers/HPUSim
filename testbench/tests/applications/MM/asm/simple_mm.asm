;n = 64
mov #4 R0 
;n*n 
mul R0 R0 R3

; matrix multiplication - P*A
;i
mov #0 R1 
;for i=0;i<n;i++ --offset 22
lbeg #18 R0 R1
;j
mov #0 R2
;for j=0;j<n;j++
lbeg #14 R0 R2
;i*n+j
mul R1 R0 R8 
add R8 R2 R9
;Aprimematrix+i*n+j
add #30000000 R9 R10 
;k
mov #0 R7 
;tmp sum
mov #0 R11
lbeg #B R0 R7
;i*n+k
add R7 R8 R12
;pivotmatrix + i*n+k--> a[i][k]
add #10000000 R12 R13 
;load a[i][k]
lw R13 R16
; k*n+j
mul R7 R2 R14
; inputmatrix+k*n+j -->b[k][j]
add #20000000 R14 R15
;load b[k][j]
lw R15 R17
; a*b
mul R16 R17 R18
;c = c+a*b
add R18 R11 R11
;k++
add R7 #1 R7 
lend
;store c to aprimematrix+j*n+j
sw R11 R10
;j++
add R2 #1 R2
lend
;i++
add R1 #1 R1
lend
;matrix multiplication of the P*A ends here..
mov R21 R22
end
