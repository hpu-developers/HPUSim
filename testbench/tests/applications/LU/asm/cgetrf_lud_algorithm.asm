;n = 4
mov #4 R0 
;n*n 
mul R0 R0 R3
;i=0
mov #0 R1
;L matrix zeroed
;lw/sw 4Bytes
;Store 0 to L and U matrix ;TODO: Memory address
for i=0;i<n*n;i++
lbeg #4 R3 R1
sw #0 #01000000
add R1 #1 R1
lend
;i=0
mov #0 R1
; for i =0;i<n*n;i++
lbeg #4 R3 R1 
sw #0 #0A000000
add R1 #1 R1
lend

;pivot function starts here.... 
;R0 --> 64
;i=0
mov #0 R1
;for i=0; i<n;i++
lbeg #B R0 R1
;j=0
mov #0 R2
; for j =0;j<n;j++
lbeg #7 R0 R2
; i==j true --> 1 no -> 0
cmp R1 R2 R6
;i*n
mul R1 R0 R4
;i*n+j
add R4 R2 R5
;pmatrix + i*n+j
add #10000000 R5 R55
;p[i*n+j] = (i==j) - commented as stored dont add latency -kvn
;sw R6 R55 
;j++ 
add R2 #1 R2
;j end
lend
;i++
add R1 #1 R1
;i end
lend
; ----- ABOVE THIS IS CLEAR
;i=0
mov #0 R1
;for i=0;i<n;i++
lbeg #20 R0 R1
; max_j = i -> R4 is duplicate
mov R1 R4
;j=i
mov R1 R5 
; for j=i j<n;j++
lbeg #D R0 R5
;j*n
mul R5 R0 R6 
;j*n+i
add R6 R1 R7 
;max_j*n
mul R4 R0 R8
; max_j*n+i
add R8 R1 R9
;*a[j][i]
add #20000000 R7 R10
; val in a[j][i]
lw R10 R11
;*a[mat_j][i]
add #20000000 R8 R12
; val in a[mat_j][i]
lw R12 R13
; if branch less than equal to go to offset
;ble #4 R11 R13 
; max_j =j
mov R5 R4
;j++
add R5 #1 R5
lend

; max_j !=i --> taken branch
; perform swap opertion
beq #E R4 R1 
;k=0
mov #0 R14
; for k=0; k<n;k++
lbeg #C R0 R14
;i*n
mul R1 R0 R15 
;i*n+k
add R15 R14 R16 
;pmatrix+i*n+k
add #10000000 R16 R17 
;tmp 
lw R17 R18
;max_j*n+k 
add R8 R14 R19 
; pmatrix+max_j*n+k
add #10000000 R19 R20
;load 
lw R20 R21
; p[i*n+k] = p[max_j*n+k]
sw R21 R17
; p[max_j*n+k] = tmp 
sw R18 R20 
;k++
add R14 #1 R14 
lend
;i++
add R1 #1 R1
lend

; --------------- ABOVE is clear
;pivot function ends here.... 

; matrix multiplication - P*A
;i
mov #0 R1 
;for i=0;i<n;i++ --offset 21
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
; ---------------- ABOVE IS CLEAR

;;L[i][i]=1 operation
;;i
;mov #0 R1
;lbeg #7 R0 R1
;;i*n+i
;mul R1 R0 R2
;add R2 R1 R11
;;lmatrix+i*n+i
;add #01000000 R11 R12
;sw #1 R12
;add R1 #1 R1
;lend
;
;;lu operations
;;ij
;mov #0 R1 
;lbeg #B R0 R1
;mov #0 R2
;lbeg #7 R0 R2
;;i*n
;mul R1 R0 R12
;;j*n
;mul R2 R0 R13
;; j<=i
;ble #7 R2 R1 
;ble #1B R1 R2 
;add R2 #1 R2
;lend
;add R1 #1 R1
;lend
;
;
;jmp #30
;
;;true: j<=i
;;s=0
;mov #0 R11
;;k=0 
;mov #0 R7
;;for k=0;k<j;k++
;lbeg #C R2 R7
;;j*n+k
;add R13 R7 R14
;;lmatrix+j*n+k 
;add #01000000 R14 R14
;; L[j*n+k]
;lw #01000000 R15
;;k*n
;mul R7 R0 R16 
;;k*n+i
;add R16 R1 R17
;;umatrix+k*n*i
;add #0A000000 R17 R17
;;U[k*n+i]
;lw R17 R18
;; L*U
;mul R18 R15 R19
;;s+=L*U 
;add R11 R19 R11
;add R7 #1 R7
;lend
;
;;j*n+i
;add R13 R1 R20
;;U[j*n+i]
;add #0A000000 R20 R21
;;*Aprime[j*n+i]
;add #30000000 R20 R22
;;Aprime[j*n+i]
;lw R22 R23
;; Aprime[j*n+i]-s
;sub R23 R11 R24
;;U =Aprime -s 
;sw R24 R21
;;go to j>=i case check
;jmp #-1A 
;
;;----------------------------------
;;j>=i true case
;;s=0
;mov #0 R11
;;k=0 
;mov #0 R7
;;for k=0;k<i;k++
;lbeg #C R1 R7
;;j*n+k
;add R13 R7 R14
;;lmatrix+j*n+k 
;add #01000000 R14 R14
;; L[j*n+k]
;lw #01000000 R15
;;k*n
;mul R7 R0 R16 
;;k*n+i
;add R16 R1 R17
;;umatrix+k*n*i
;add #0A000000 R17 R17
;;U[k*n+i]
;lw R17 R18
;; L*U
;mul R18 R15 R19
;;s+=L*U 
;add R11 R19 R11
;add R7 #1 R7
;lend
;
;;j*n+i
;add R13 R1 R20
;;L[j*n+i]
;add #01000000 R20 R21
;;*Aprime[j*n+i]
;add #30000000 R20 R22
;;Aprime[j*n+i]
;lw R22 R23
;; Aprime[j*n+i]-s
;sub R23 R11 R24
;;i*n+i
;add R12 R1 R25
;;*U[i*n+i]
;add #0A000000 R25 R26
;;load U[i*n+i]
;lw R26 R27 
;; Aprime/U
;div R24 R27 R28
;;U =Aprime -s 
;sw R28 R21
;;go to j>=i case check
;jmp #-32
;;
;;dummy end of program
;add #0 R1 R29
mov R50 R51 
end
;
;
;;mat_LU(double** double** double** double** int):
;;      test    r8d r8d
;;      jle     .L57
;;      push    r15
;;      movsd   xmm5 QWORD PTR .LC1[rip]
;;      mov     r15 rsi
;;      mov     r9 rdi
;;      push    r14
;;      mov     rsi rdx
;;      push    r13
;;      lea     r13d [r8-1]
;;      push    r12
;;      lea     r14 [r13+1]
;;      push    rbp
;;      mov     rbp rcx
;;      xor     ecx ecx
;;      push    rbx
;;      mov     DWORD PTR [rsp-20] r13d
;;.L7:
;;      mov     rdi QWORD PTR [rbp+0+rcx*8]
;;      xor     eax eax
;;      jmp     .L6
;;.L61:
;;      mov     QWORD PTR [rdi+rax*8] 0x000000000
;;      lea     rdx [rax+1]
;;      cmp     rax r13
;;      je      .L4
;;.L5:
;;      mov     rax rdx
;;.L6:
;;      cmp     eax ecx
;;      jne     .L61
;;      movsd   QWORD PTR [rdi+rax*8] xmm5
;;      lea     rdx [rax+1]
;;      cmp     rax r13
;;      jne     .L5
;;.L4:
;;      lea     rax [rcx+1]
;;      cmp     rcx r13
;;      je      .L62
;;      mov     rcx rax
;;      jmp     .L7
;;.L62:
;;      mov     r12d r8d
;;      mov     ebx r8d
;;      movq    xmm1 QWORD PTR .LC2[rip]
;;      xor     edi edi
;;      and     r12d -2
;;      shr     ebx
;;      mov     r11d r12d
;;      sal     rbx 4
;;      sal     r11 3
;;.L10:
;;      mov     rax QWORD PTR [r9+rdi*8]
;;      mov     ecx edi
;;      lea     r10 [0+rdi*8]
;;      movsd   xmm4 QWORD PTR [rax+rdi*8]
;;      mov     rax rdi
;;      movapd  xmm0 xmm4
;;      jmp     .L8
;;.L63:
;;      movsx   rdx ecx
;;      add     rax 1
;;      sal     rdx 3
;;      cmp     r8d eax
;;      jle     .L12
;;.L64:
;;      mov     rdx QWORD PTR [r9+rax*8]
;;      movsd   xmm0 QWORD PTR [rdx+r10]
;;.L8:
;;      movapd  xmm3 xmm0
;;      movapd  xmm2 xmm4
;;      lea     rdx [0+rax*8]
;;      andpd   xmm3 xmm1
;;      andpd   xmm2 xmm1
;;      comisd  xmm3 xmm2
;;      jbe     .L63
;;      mov     ecx eax
;;      add     rax 1
;;      movapd  xmm4 xmm0
;;      cmp     r8d eax
;;      jg      .L64
;;.L12:
;;      cmp     ecx edi
;;      jne     .L65
;;.L13:
;;      lea     rax [rdi+1]
;;      cmp     rdi r13
;;      je      .L9
;;.L66:
;;      mov     rdi rax
;;      jmp     .L10
;;.L65:
;;      mov     rax QWORD PTR [rbp+0+rdi*8]
;;      mov     rdx QWORD PTR [rbp+0+rdx]
;;      lea     rcx [rax+15]
;;      sub     rcx rdx
;;      cmp     rcx 30
;;      mov     ecx 0
;;      jbe     .L14
;;      cmp     DWORD PTR [rsp-20] 1
;;      jbe     .L14
;;.L15:
;;      movupd  xmm0 XMMWORD PTR [rax+rcx]
;;      movupd  xmm6 XMMWORD PTR [rdx+rcx]
;;      movups  XMMWORD PTR [rax+rcx] xmm6
;;      movups  XMMWORD PTR [rdx+rcx] xmm0
;;      add     rcx 16
;;      cmp     rbx rcx
;;      jne     .L15
;;      cmp     r12d r8d
;;      je      .L13
;;      add     rax r11
;;      add     rdx r11
;;      movsd   xmm0 QWORD PTR [rax]
;;      movsd   xmm2 QWORD PTR [rdx]
;;      movsd   QWORD PTR [rax] xmm2
;;      lea     rax [rdi+1]
;;      movsd   QWORD PTR [rdx] xmm0
;;      cmp     rdi r13
;;      jne     .L66
;;.L9:
;;      sal     r14 3
;;      xor     eax eax
;;.L18:
;;      mov     rdx QWORD PTR [r15+rax]
;;      movsd   QWORD PTR [rdx+rax] xmm5
;;      add     rax 8
;;      cmp     r14 rax
;;      jne     .L18
;;      mov     QWORD PTR [rsp-16] r13
;;      mov     r14 rsi
;;      xor     ebx ebx
;;      pxor    xmm3 xmm3
;;      mov     DWORD PTR [rsp-24] -1
;;.L36:
;;      mov     edi DWORD PTR [rsp-20]
;;      mov     r11d DWORD PTR [rsp-24]
;;      lea     rax [0+rbx*8]
;;      mov     r12d ebx
;;      cmp     edi ebx
;;      mov     r13d edi
;;      cmovg   r13d ebx
;;      xor     ecx ecx
;;.L27:
;;      mov     ebp ecx
;;      test    rcx rcx
;;      je      .L67
;;      mov     rdi QWORD PTR [r15+rcx*8]
;;      lea     r10d [rcx-1]
;;      xor     edx edx
;;      movapd  xmm1 xmm3
;;.L23:
;;      mov     r9 QWORD PTR [rsi+rdx*8]
;;      movsd   xmm0 QWORD PTR [r9+rax]
;;      mulsd   xmm0 QWORD PTR [rdi+rdx*8]
;;      mov     r9 rdx
;;      add     rdx 1
;;      addsd   xmm1 xmm0
;;      cmp     r9 r10
;;      jne     .L23
;;.L19:
;;      xor     edx edx
;;      mov     rdx QWORD PTR [rdx+rcx*8]
;;      movsd   xmm2 QWORD PTR [rdx+rax]
;;      mov     rdx QWORD PTR [rsi+rcx*8]
;;      movapd  xmm0 xmm2
;;      subsd   xmm0 xmm1
;;      movsd   QWORD PTR [rdx+rax] xmm0
;;      cmp     r12d ebp
;;      jle     .L68
;;.L25:
;;      lea     edx [rcx+1]
;;      add     rcx 1
;;      cmp     r13d ecx
;;      jge     .L27
;;      cmp     r8d edx
;;      jle     .L30
;;      mov     r11 QWORD PTR [r14]
;;      mov     r10d DWORD PTR [rsp-24]
;;      movsx   rcx edx
;;.L31:
;;      test    rbx rbx
;;      je      .L69
;;      mov     r9 QWORD PTR [r15+rcx*8]
;;      xor     edx edx
;;      movapd  xmm1 xmm3
;;.L33:
;;      mov     rdi QWORD PTR [rsi+rdx*8]
;;      movsd   xmm0 QWORD PTR [rdi+rax]
;;      mulsd   xmm0 QWORD PTR [r9+rdx*8]
;;      mov     rdi rdx
;;      add     rdx 1
;;      addsd   xmm1 xmm0
;;      cmp     rdi r10
;;      jne     .L33
;;.L32:
;;      xor     edx edx
;;      mov     rdx QWORD PTR [rdx+rcx*8]
;;      add     rcx 1
;;      movsd   xmm0 QWORD PTR [rdx+rax]
;;      subsd   xmm0 xmm1
;;      divsd   xmm0 QWORD PTR [r11+rax]
;;      movsd   QWORD PTR [r9+rax] xmm0
;;      cmp     r8d ecx
;;      jg      .L31
;;.L30:
;;      add     DWORD PTR [rsp-24] 1
;;      lea     rax [rbx+1]
;;      add     r14 8
;;      cmp     rbx QWORD PTR [rsp-16]
;;      je      .L1
;;      mov     rbx rax
;;      jmp     .L36
;;.L14:
;;      movsd   xmm0 QWORD PTR [rax+rcx*8]
;;      movsd   xmm2 QWORD PTR [rdx+rcx*8]
;;      mov     r10 rcx
;;      movsd   QWORD PTR [rax+rcx*8] xmm2
;;      movsd   QWORD PTR [rdx+rcx*8] xmm0
;;      add     rcx 1
;;      cmp     r10 r13
;;      jne     .L14
;;      jmp     .L13
;;.L68:
;;      test    r12d r12d
;;      je      .L70
;;      mov     rdi QWORD PTR [r15+rcx*8]
;;      xor     edx edx
;;      movapd  xmm1 xmm3
;;.L26:
;;      mov     r9 QWORD PTR [rsi+rdx*8]
;;      movsd   xmm0 QWORD PTR [r9+rax]
;;      mulsd   xmm0 QWORD PTR [rdi+rdx*8]
;;      mov     r9 rdx
;;      add     rdx 1
;;      addsd   xmm1 xmm0
;;      cmp     r9 r11
;;      jne     .L26
;;.L21:
;;      mov     rdx QWORD PTR [r14]
;;      subsd   xmm2 xmm1
;;      divsd   xmm2 QWORD PTR [rdx+rax]
;;      movsd   QWORD PTR [rdi+rax] xmm2
;;      jmp     .L25
;;.L69:
;;      mov     r9 QWORD PTR [r15+rcx*8]
;;      movapd  xmm1 xmm3
;;      jmp     .L32
;;.L67:
;;      movapd  xmm1 xmm3
;;      jmp     .L19
;;.L70:
;;      mov     rdi QWORD PTR [r15+rcx*8]
;;      movapd  xmm1 xmm3
;;      jmp     .L21
;;.L1:
;;      pop     rbx
;;      pop     rbp
;;      pop     r12
;;      pop     r13
;;      pop     r14
;;      pop     r15
;;      ret
;;.L57:
;;      ret
;;main:
;;      sub     rsp 8
;;      mov     r8d 1024
;;      xor     ecx ecx
;;      xor     edx edx
;;      xor     esi esi
;;      xor     edi edi
;;      call    mat_LU(double** double** double** double** int)
;;      xor     eax eax
;;      add     rsp 8
;;      ret
;;.LC1:
;;      .long   0
;;      .long   1072693248
;;.LC2:
;;      .long   4294967295
;;      .long   2147483647
;;      .long   0
;;      .long   0
