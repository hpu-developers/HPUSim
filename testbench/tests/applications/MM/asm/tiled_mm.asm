; block size = 16
mov #16 R0
;N = 40
mov #40 R1
;K= 40
mov #40 R2
;M = 40
mov #40 R3
;i=0
mov #0 R4

; LOOP 0 Begin
;for i..i<N,i++
lbeg #B R1 R4
;j=0
mov #0 R5
;for j..j<K,j++
; LOOP 1 BEGIN
lbeg #7 R2 R5
;K*i
mul R2 R4 R6
;K*i+j
add R6 R5 R7
;cmatrix+K*i+j
add #A0000000 R7 R8 
;c=0
sw #0 R8
;j++
add R5 #1 R5
lend
; LOOP 1 END
;i++
add R4 #1 R4
lend
 ; LOOP 0 End
;i0=0
mov #0 R4

; LOOP BEG  - 53 Offset
lbeg #35 R1 R4
; i0 + blocksize
add R4 R0 R10
;i0+bs <=N
ble #3 R10 R1
;imax = N
mov R1 R11
; jump
jmp #2
;imax = i0+blocksize
mov R10 R11
;j0=0
mov #0 R5
;for j ;j<M Offset: 44
lbeg #2C R3 R5
; j0 + blocksize
add R5 R0 R12
;j0+bs <=M
ble #3 R12 R3
;jmax = N
mov R3 R13
; jump
jmp #2
;jmax = j0+blocksize
mov R12 R13
;k0=0
mov #0 R6
;for k ;k<K - 0x24
lbeg #23 R2 R6
; k0 + blocksize
add R6 R0 R14
;k0+bs <=M
ble #3 R14 R2
;kmax = N
mov R2 R15
; jump
jmp #2
;kmax = k0+blocksize
mov R14 R15
;j1=j0
mov R5 R7
;for j1=j0 j1<jmax j1++ - 26
lbeg #1A R13 R7
;sj = M*j1
mul R7 R3 R16
;i1=i0
mov R4 R8
;for i1=i0 i1<imax i1++ - 21
lbeg #15 R11 R8
;mi = M*i1
mul R3 R8 R17 
;ki = K*i1
mul R2 R8 R18
;kij = ki + j1
add R18 R7 R19
;cmatrix+kij
add #A0000000 R19 R26
;load C[kij]
lw R26 R28
;k1=k0
mov R6 R9
;for k1=i0 k1<kmax k1++ - 13
lbeg #C R15 R9
;mi+k1
add R9 R17 R20
;*A
add #10000000 R20 R21
;A[mi+k1]
lw R21 R22
;sj+k1
add R16 R9 R23 
;*B
add #20000000 R23 R24
;B[sj+k1]
lw R24 R25 
;A*B
mul R25 R22 R27
;add C[kij]+A*B
add R28 R27 R29
;write to cmatrix
sw R29 R26
;k1++
add R9 #1 R9
; Loop end
lend
;i1++
add R8 #1 R8
; Loop end
lend
;j1++
add R7 #1 R7 
; Loop end
lend
;k0+=blocksize
add R6 R0 R6 
; Loop end
lend 
;j0+=blocksize 
add R5 R0 R5 
; Loop end
lend 
;i0+=blocksize 
add R4 R0 R4
; Loop end
lend 
mov R91 R92
end
